"""Planner agent that decomposes goals and delegates to specialists."""

import json
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from agents.base import BaseAgent
from agents.research import ResearchAgent
from agents.code import CodeAgent
from agents.data import DataAgent
from database import create_task, update_task
from websocket.manager import (
    broadcast_agent_status,
    broadcast_task_created,
    broadcast_task_updated,
    broadcast_log,
    broadcast_memory_write,
)
from memory.qdrant_store import QdrantMemoryStore


class PlannerState(TypedDict):
    """State for planner agent."""
    goal: str
    task_ids: List[str]
    subtasks: List[Dict]
    current_index: int
    results: List[str]
    status: str
    progress: float
    parent_task_id: str


class PlannerAgent(BaseAgent):
    """Planner agent that decomposes tasks and coordinates sub-agents."""

    def __init__(self):
        super().__init__(
            agent_id="planner",
            name="Planner",
            role="planner",
            description="Decomposes goals into subtasks and routes them to specialists",
        )

        self.tools = ["task-graph", "router"]

        # Initialize sub-agents
        self.research_agent = ResearchAgent()
        self.code_agent = CodeAgent()
        self.data_agent = DataAgent()
        self.memory_store = QdrantMemoryStore()

        # Build workflow
        self.workflow = self._build_workflow()

    @property
    def sub_agents(self):
        """Map of agent ID to agent instance."""
        return {
            "research": self.research_agent,
            "code": self.code_agent,
            "data": self.data_agent,
        }

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        builder = StateGraph(PlannerState)

        builder.add_node("decompose", self._decompose_node)
        builder.add_node("delegate", self._delegate_node)
        builder.add_node("execute_subtask", self._execute_subtask_node)
        builder.add_node("collect", self._collect_node)
        builder.add_node("finalize", self._finalize_node)

        builder.set_entry_point("decompose")
        builder.add_edge("decompose", "delegate")
        builder.add_edge("delegate", "execute_subtask")
        builder.add_conditional_edges(
            "execute_subtask",
            self._has_more_subtasks,
            {"continue": "execute_subtask", "done": "collect"},
        )
        builder.add_edge("collect", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile(checkpointer=MemorySaver())

    async def _decompose_node(self, state: PlannerState) -> PlannerState:
        """Decompose the goal into subtasks."""
        await self.set_status("thinking", state["parent_task_id"])
        await broadcast_task_updated(state["parent_task_id"], {"status": "planning"})
        await self.log(f"Decomposing goal: {state['goal'][:60]}...")

        # Get relevant past memories
        try:
            memories = await self.memory_store.search(
                query=state["goal"],
                limit=3,
            )
            memory_context = ""
            if memories:
                memory_context = "\n\nRelevant past outcomes:\n" + "\n".join([
                    f"- {m.get('summary', '')}"
                    for m in memories
                ])
        except Exception:
            memory_context = ""

        prompt = f"""You are a task planner. Decompose this goal into 2-4 specific subtasks:

Goal: {state['goal']}
{memory_context}

For each subtask, determine the best agent:
- "research" for web search, information gathering
- "code" for file operations, coding tasks
- "data" for database queries, retrieval tasks

Output as JSON array:
[{{"description": "what to do", "agent": "research|code|data", "reason": "why this agent"}}]

Keep subtasks concrete and actionable."""

        response = await self.llm.ainvoke([
            SystemMessage(content="You are a task decomposition planner. Output valid JSON only."),
            HumanMessage(content=prompt)
        ])

        # Parse subtasks
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            subtasks = json.loads(content.strip())
            if not isinstance(subtasks, list):
                subtasks = [subtasks]

        except Exception as e:
            await self.log(f"Parse error, using fallback: {e}")
            # Fallback decomposition
            subtasks = self._fallback_decomposition(state["goal"])

        await self.log(f"Created {len(subtasks)} subtasks")
        for i, st in enumerate(subtasks):
            await self.log(f"  {i+1}. [{st.get('agent', 'unknown')}] {st.get('description', 'unnamed')[:40]}...")

        return {**state, "subtasks": subtasks, "current_index": 0, "progress": 20}

    def _fallback_decomposition(self, goal: str) -> List[Dict]:
        """Simple rule-based fallback decomposition."""
        goal_lower = goal.lower()

        if any(w in goal_lower for w in ["search", "find", "look up", "research"]):
            return [{"description": goal, "agent": "research", "reason": "information gathering"}]
        elif any(w in goal_lower for w in ["code", "write", "create file", "script"]):
            return [{"description": goal, "agent": "code", "reason": "file/code operation"}]
        elif any(w in goal_lower for w in ["query", "search database", "retrieve", "similar"]):
            return [{"description": goal, "agent": "data", "reason": "data retrieval"}]
        else:
            return [
                {"description": f"Research: {goal}", "agent": "research", "reason": "initial research"},
                {"description": f"Compile findings for: {goal}", "agent": "code", "reason": "synthesis"},
            ]

    async def _delegate_node(self, state: PlannerState) -> PlannerState:
        """Create task records for subtasks."""
        await self.set_status("active", state["parent_task_id"])

        task_ids = []
        for subtask in state["subtasks"]:
            agent_id = subtask.get("agent", "research")
            description = subtask.get("description", "Unnamed subtask")

            # Create task in database
            task = await create_task(
                goal=description,
                assigned_agent_id=agent_id,
                parent_task_id=state["parent_task_id"],
                status="queued",
            )

            task_ids.append(task.id)

            # Broadcast task creation
            await broadcast_task_created({
                "id": task.id,
                "goal": description,
                "assignedAgentId": agent_id,
                "status": "queued",
                "progress": 0,
                "startedAt": None,
                "parentTaskId": state["parent_task_id"],
            })

        await self.log(f"Created {len(task_ids)} subtask records")

        return {**state, "task_ids": task_ids, "results": [None] * len(task_ids), "progress": 30}

    async def _execute_subtask_node(self, state: PlannerState) -> PlannerState:
        """Execute current subtask."""
        idx = state["current_index"]
        if idx >= len(state["subtasks"]):
            return {**state, "progress": 80}

        subtask = state["subtasks"][idx]
        task_id = state["task_ids"][idx]
        agent_id = subtask.get("agent", "research")
        goal = subtask.get("description", "")

        await self.log(f"Delegating to {agent_id}: {goal[:50]}...")

        # Get agent and execute
        agent = self.sub_agents.get(agent_id)
        if not agent:
            await self.log(f"Unknown agent: {agent_id}")
            state["results"][idx] = f"Error: Unknown agent {agent_id}"
        else:
            try:
                result = await agent.execute(task_id, goal, context={"parent_goal": state["goal"]})
                state["results"][idx] = result
            except Exception as e:
                await self.log(f"Subtask failed: {e}")
                state["results"][idx] = f"Error: {str(e)}"

        # Update progress
        progress = 30 + int((idx + 1) / len(state["subtasks"]) * 50)

        return {**state, "current_index": idx + 1, "progress": progress}

    def _has_more_subtasks(self, state: PlannerState) -> str:
        """Check if there are more subtasks to execute."""
        if state["current_index"] < len(state["subtasks"]):
            return "continue"
        return "done"

    async def _collect_node(self, state: PlannerState) -> PlannerState:
        """Collect and synthesize results."""
        await self.set_status("thinking", state["parent_task_id"])
        await self.log("Synthesizing results from all subtasks...")

        # Combine results
        synthesis_parts = []
        for i, (subtask, result) in enumerate(zip(state["subtasks"], state["results"])):
            agent = subtask.get("agent", "unknown")
            synthesis_parts.append(f"## Subtask {i+1} ({agent})\n{result}")

        combined = "\n\n".join(synthesis_parts)

        # Final synthesis via LLM
        prompt = f"""Synthesize these results into a coherent final answer for the goal:

Goal: {state['goal']}

Results:
{combined[:3000]}

Provide a concise final summary (2-3 paragraphs)."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        final_synthesis = response.content

        return {**state, "synthesis": final_synthesis, "status": "complete", "progress": 95}

    async def _finalize_node(self, state: PlannerState) -> PlannerState:
        """Finalize and write to memory."""
        await self.log("Task complete, writing to memory...")

        # Write outcome to memory
        try:
            memory_summary = f"Goal: {state['goal'][:80]}... Result: {state.get('synthesis', 'Complete')[:80]}..."
            memory_content = f"""Goal: {state['goal']}

Outcome:
{state.get('synthesis', 'Task completed')}

Subtasks: {len(state['subtasks'])}
Status: Success
"""
            memory_id = await self.memory_store.write(
                content=memory_content,
                summary=memory_summary,
                kind="outcome",
                task_id=state["parent_task_id"],
                agent_id="planner",
            )

            await broadcast_memory_write(memory_id, memory_summary, "outcome")
            await self.log(f"Written to memory: {memory_id[:8]}...")

        except Exception as e:
            await self.log(f"Memory write failed: {e}")

        await self.set_status("idle", None)
        return {**state, "progress": 100}

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Execute planning workflow - this is triggered by /api/tasks/plan."""
        # For planning, the parent_task_id IS the task_id from the API
        initial_state: PlannerState = {
            "goal": goal,
            "task_ids": [],
            "subtasks": [],
            "current_index": 0,
            "results": [],
            "status": "running",
            "progress": 5,
            "parent_task_id": task_id,
        }

        # Thread ID for checkpointing
        config = {"configurable": {"thread_id": task_id}}

        try:
            final_state = await self.workflow.ainvoke(initial_state, config)

            # Mark parent task complete
            await update_task(
                task_id,
                status="done",
                progress=100,
                result=final_state.get("synthesis", "Complete"),
            )

            await broadcast_task_updated(task_id, {"status": "done", "progress": 100})

            return final_state.get("synthesis", "Task planning complete")

        except Exception as e:
            await self.log(f"Planning error: {str(e)}")
            await update_task(task_id, status="failed", progress=0, result=str(e))
            await broadcast_task_updated(task_id, {"status": "failed", "progress": 0})
            await self.set_status("error", None)
            raise

    async def create_plan(self, goal: str) -> List[str]:
        """Create a plan without executing (returns task IDs)."""
        # This is called from the API endpoint
        # The actual task is created by the API, we just kick off execution
        task = await create_task(
            goal=goal,
            assigned_agent_id="planner",
            status="planning",
        )

        # Broadcast parent task created
        await broadcast_task_created({
            "id": task.id,
            "goal": goal,
            "assignedAgentId": "planner",
            "status": "planning",
            "progress": 5,
            "parentTaskId": None,
        })

        return task.id

    def get_agent_info(self):
        """Get agent info with correct tools."""
        return {
            **super().get_agent_info(),
            "toolsUsed": ["task-graph", "router"],
        }
