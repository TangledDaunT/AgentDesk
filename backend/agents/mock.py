"""Mock agent implementations for testing without API keys."""

import asyncio
import random
from typing import Dict, Any
from datetime import datetime

from agents.base import BaseAgent
from database import update_task
from websocket.manager import (
    broadcast_agent_status,
    broadcast_log,
    broadcast_task_updated,
    broadcast_memory_write,
)
from memory.qdrant_store import QdrantMemoryStore


class MockPlannerAgent(BaseAgent):
    """Mock planner that simulates task decomposition."""

    def __init__(self):
        super().__init__(
            agent_id="planner",
            name="Planner",
            role="planner",
            description="Decomposes goals into subtasks (MOCK MODE)",
        )
        self.memory_store = QdrantMemoryStore()

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Simulate planning workflow."""
        await self.set_status("thinking", task_id)
        await broadcast_task_updated(task_id, {"status": "planning"})
        await self.log(f"[MOCK] Planning: {goal[:60]}...")

        # Simulate decomposition delay
        await asyncio.sleep(1)

        # Create mock subtasks
        from database import create_task

        subtasks = [
            {"desc": f"Research: {goal}", "agent": "research"},
            {"desc": f"Process findings for: {goal}", "agent": "code"},
        ]

        await self.log(f"[MOCK] Created {len(subtasks)} subtasks")

        for i, subtask in enumerate(subtasks):
            task = await create_task(
                goal=subtask["desc"],
                assigned_agent_id=subtask["agent"],
                parent_task_id=task_id,
                status="queued",
            )
            await broadcast_log("planner", f"  Subtask {i+1}: [{subtask['agent']}] {subtask['desc'][:40]}...")
            await asyncio.sleep(0.3)

        # Simulate execution
        await self.set_status("active", task_id)
        await asyncio.sleep(1)

        # Complete
        result = f"[MOCK] Completed planning for: {goal}\n\nCreated {len(subtasks)} subtasks and simulated execution."

        await update_task(task_id, status="done", progress=100, result=result)
        await broadcast_task_updated(task_id, {"status": "done", "progress": 100})

        # Write to memory
        try:
            memory_id = await self.memory_store.write(
                content=result,
                summary=f"[MOCK] Planned: {goal[:60]}...",
                kind="outcome",
                task_id=task_id,
                agent_id="planner",
            )
            await broadcast_memory_write(memory_id, f"[MOCK] Planned: {goal[:60]}...", "outcome")
        except Exception:
            pass

        await self.set_status("idle", None)
        return result

    def get_agent_info(self):
        return {
            **super().get_agent_info(),
            "toolsUsed": ["task-graph (mock)", "router (mock)"],
        }


class MockResearchAgent(BaseAgent):
    """Mock research agent."""

    def __init__(self):
        super().__init__(
            agent_id="research",
            name="Research agent",
            role="research",
            description="Web search via MCP (MOCK MODE)",
        )

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        await self.set_status("thinking", task_id)
        await self.update_task_progress(task_id, "running", 10)
        await self.log(f"[MOCK] Searching: {goal[:60]}...")

        # Simulate search
        await asyncio.sleep(1.5)
        await self.set_status("active", task_id)
        await self.update_task_progress(task_id, "running", 50)

        # Mock results
        results = [
            "Found 5 relevant sources",
            "Top result: Example documentation",
            "Synthesized key findings",
        ]

        for r in results:
            await self.log(f"[MOCK] {r}")
            await asyncio.sleep(0.3)

        await self.update_task_progress(task_id, "running", 90)
        await asyncio.sleep(0.5)

        result = f"[MOCK] Research complete for: {goal}\n\nSimulated web search returned 5 results. Key finding: This is mock data for UI testing."

        await self.update_task_progress(task_id, "done", 100, result)
        await self.set_status("idle", None)
        return result

    def get_agent_info(self):
        return {
            **super().get_agent_info(),
            "toolsUsed": ["web_search (mock)", "web_fetch (mock)"],
        }


class MockCodeAgent(BaseAgent):
    """Mock code agent."""

    def __init__(self):
        super().__init__(
            agent_id="code",
            name="Code agent",
            role="code",
            description="File operations via MCP (MOCK MODE)",
        )

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        await self.set_status("thinking", task_id)
        await self.update_task_progress(task_id, "running", 10)
        await self.log(f"[MOCK] Coding: {goal[:60]}...")

        await asyncio.sleep(1)
        await self.set_status("active", task_id)
        await self.update_task_progress(task_id, "running", 40)

        await self.log("[MOCK] Writing file: mock_output.py")
        await asyncio.sleep(0.5)

        await self.update_task_progress(task_id, "running", 70)
        await self.log("[MOCK] File written (256 bytes)")

        await asyncio.sleep(0.5)

        result = f"[MOCK] Code task complete: {goal}\n\nCreated mock_output.py with simulated implementation."

        await self.update_task_progress(task_id, "done", 100, result)
        await self.set_status("idle", None)
        return result

    def get_agent_info(self):
        return {
            **super().get_agent_info(),
            "toolsUsed": ["fs_read (mock)", "fs_write (mock)", "shell (mock)"],
        }


class MockDataAgent(BaseAgent):
    """Mock data agent."""

    def __init__(self):
        super().__init__(
            agent_id="data",
            name="Data agent",
            role="data",
            description="Qdrant queries via MCP (MOCK MODE)",
        )

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        await self.set_status("thinking", task_id)
        await self.update_task_progress(task_id, "running", 20)
        await self.log(f"[MOCK] Querying: {goal[:60]}...")

        await asyncio.sleep(1)
        await self.set_status("active", task_id)

        # Try real Qdrant query if available
        try:
            from tools.qdrant_client import query_memory
            results = await query_memory(goal, limit=3)
            await self.log(f"[MOCK/API] Retrieved {len(results)} results from Qdrant")
        except Exception as e:
            await self.log(f"[MOCK] Simulated query (Qdrant: {e})")
            results = []

        await self.update_task_progress(task_id, "running", 80)
        await asyncio.sleep(0.5)

        result = f"[MOCK] Data retrieval complete: {goal}\n\nRetrieved {len(results)} documents from vector store."

        await self.update_task_progress(task_id, "done", 100, result)
        await self.set_status("idle", None)
        return result

    def get_agent_info(self):
        return {
            **super().get_agent_info(),
            "toolsUsed": ["qdrant_query (mock)", "sql_query (mock)"],
        }
