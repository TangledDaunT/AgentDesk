"""Data agent with Qdrant query capabilities."""

from typing import Dict, Any, List

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from agents.base import BaseAgent
from tools.qdrant_client import query_memory, add_to_memory


class DataState(TypedDict):
    """State for data agent."""
    task_id: str
    goal: str
    query_text: str
    results: List[Dict]
    analysis: str
    status: str
    progress: float


class DataAgent(BaseAgent):
    """Agent that queries Qdrant for retrieval tasks."""

    def __init__(self):
        super().__init__(
            agent_id="data",
            name="Data agent",
            role="data",
            description="Queries Qdrant and Postgres for structured retrieval",
        )

        self.tools = ["qdrant_query", "sql_query"]

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        builder = StateGraph(DataState)

        builder.add_node("parse_query", self._parse_query_node)
        builder.add_node("execute_query", self._execute_query_node)
        builder.add_node("analyze_results", self._analyze_results_node)

        builder.set_entry_point("parse_query")
        builder.add_edge("parse_query", "execute_query")
        builder.add_edge("execute_query", "analyze_results")
        builder.add_edge("analyze_results", END)

        return builder.compile()

    async def _parse_query_node(self, state: DataState) -> DataState:
        """Parse the query from the goal."""
        await self.set_status("thinking", state["task_id"])
        await self.update_task_progress(state["task_id"], "running", 10)
        await self.log("Parsing retrieval query...")

        # Extract query text from goal
        goal = state["goal"].lower()

        if "similar" in goal or "top" in goal or "retriev" in goal:
            # RAG-style query
            prompt = f"""Extract the core query/keywords from this retrieval request:
{state['goal']}

Output just the search query text, nothing else."""

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            query_text = response.content.strip().strip('"')
        else:
            # Use goal as query
            query_text = state["goal"]

        await self.log(f"Query: {query_text[:60]}...")
        return {**state, "query_text": query_text, "progress": 20}

    async def _execute_query_node(self, state: DataState) -> DataState:
        """Execute Qdrant query."""
        await self.set_status("active", state["task_id"])
        await self.log("Querying vector store...")

        try:
            results = await query_memory(
                query=state["query_text"],
                limit=10,
                min_score=0.4,  # Lower threshold for broader results
            )

            await self.log(f"Found {len(results)} matching documents")

            for r in results[:3]:
                await self.log(f"  - {r.get('summary', 'unnamed')[:50]}...")

        except Exception as e:
            await self.log(f"Query error: {e}")
            results = []

        await self.update_task_progress(state["task_id"], "running", 70)
        return {**state, "results": results, "progress": 70}

    async def _analyze_results_node(self, state: DataState) -> DataState:
        """Analyze and summarize query results."""
        await self.set_status("thinking", state["task_id"])
        await self.update_task_progress(state["task_id"], "running", 90)
        await self.log("Analyzing retrieved data...")

        if not state["results"]:
            analysis = "No matching documents found in the vector store."
        else:
            # Format results for LLM
            results_text = "\n\n".join([
                f"[{i+1}] {r.get('summary', 'Unknown')}\nContent: {r.get('content', '')[:200]}"
                for i, r in enumerate(state["results"][:5])
            ])

            prompt = f"""Given this retrieval query: {state['query_text']}

Results found:
{results_text}

Provide a concise summary of the most relevant findings and their relevance scores."""

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            analysis = response.content

            # Add score info
            scores = [f"{r.get('score', 0):.2f}" for r in state["results"][:3]]
            analysis += f"\n\nTop result scores: {', '.join(scores)}"

        return {**state, "analysis": analysis, "status": "complete", "progress": 100}

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Execute data retrieval workflow."""
        initial_state: DataState = {
            "task_id": task_id,
            "goal": goal,
            "query_text": "",
            "results": [],
            "analysis": "",
            "status": "running",
            "progress": 5,
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            # Format result
            result_text = final_state["analysis"]
            if final_state["results"]:
                result_text += f"\n\nDocuments retrieved: {len(final_state['results'])}"

            await self.update_task_progress(
                task_id,
                status="done",
                progress=100,
                result=result_text,
            )

            await self.set_status("idle", None)
            return result_text

        except Exception as e:
            await self.log(f"Error: {str(e)}")
            await self.update_task_progress(task_id, status="failed", progress=0)
            await self.set_status("error", None)
            raise

    def get_agent_info(self):
        """Get agent info with correct tools."""
        return {
            **super().get_agent_info(),
            "toolsUsed": ["qdrant_query", "sql_query"],
        }
