"""Base agent class for AgentDesk."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from config import get_settings
from database import update_task
from websocket.manager import (
    broadcast_agent_status,
    broadcast_log,
    broadcast_task_updated,
)

settings = get_settings()


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, agent_id: str, name: str, role: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.1,
        )
        self.tools: List[Any] = []

    async def set_status(self, status: str, current_task: str | None = None):
        """Update agent status and broadcast."""
        await broadcast_agent_status(self.agent_id, status, current_task)

    async def log(self, text: str):
        """Log activity."""
        await broadcast_log(self.agent_id, text)

    async def update_task_progress(
        self,
        task_id: str,
        status: str | None = None,
        progress: float | None = None,
        result: str | None = None,
    ):
        """Update task and broadcast."""
        await update_task(task_id, status=status, progress=progress, result=result)

        patch = {}
        if status is not None:
            patch["status"] = status
        if progress is not None:
            patch["progress"] = progress

        if patch:
            await broadcast_task_updated(task_id, patch)

    @abstractmethod
    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Execute the agent's task."""
        pass

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent info for API response."""
        positions = {
            "planner": [0, 1.6, 0],
            "research": [-2.6, -0.6, 0.4],
            "code": [0, -1.4, -0.6],
            "data": [2.6, -0.6, 0.4],
        }

        return {
            "id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": "idle",
            "currentTask": None,
            "description": self.description,
            "toolsUsed": [t.name if hasattr(t, "name") else str(t) for t in self.tools],
            "position": positions.get(self.role, [0, 0, 0]),
        }
