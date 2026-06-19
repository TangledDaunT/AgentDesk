"""Pydantic models matching the frontend contract."""

from datetime import datetime
from typing import Literal, List
from pydantic import BaseModel, Field


# --- Agent Models ---

class Agent(BaseModel):
    """Agent state as expected by the frontend."""

    id: str
    name: str
    role: Literal["planner", "research", "code", "data"]
    status: Literal["idle", "thinking", "active", "error"]
    current_task: str | None = Field(None, alias="currentTask")
    description: str
    tools_used: List[str] = Field([], alias="toolsUsed")
    position: List[float]  # [x, y, z] for 3D graph

    model_config = {"populate_by_name": True}


class AgentStatusEvent(BaseModel):
    """WebSocket event: agent status change."""

    type: Literal["agent.status"] = "agent.status"
    agent_id: str = Field(..., alias="agentId")
    status: Literal["idle", "thinking", "active", "error"]
    current_task: str | None = Field(None, alias="currentTask")

    model_config = {"populate_by_name": True}


# --- Task Models ---

class Task(BaseModel):
    """Task state as expected by the frontend."""

    id: str
    goal: str
    assigned_agent_id: str = Field(..., alias="assignedAgentId")
    status: Literal["queued", "planning", "running", "done", "failed"]
    progress: float = Field(ge=0, le=100)
    started_at: datetime | None = Field(None, alias="startedAt")
    parent_task_id: str | None = Field(None, alias="parentTaskId")

    model_config = {"populate_by_name": True}


class TaskCreatedEvent(BaseModel):
    """WebSocket event: new task created."""

    type: Literal["task.created"] = "task.created"
    task: Task


class TaskUpdatedEvent(BaseModel):
    """WebSocket event: task state update."""

    type: Literal["task.updated"] = "task.updated"
    task_id: str = Field(..., alias="taskId")
    patch: dict


# --- Log Models ---

class LogEntry(BaseModel):
    """Activity log entry."""

    id: str
    ts: str  # timestamp as string (HH:MM:SS)
    agent_id: str = Field(..., alias="agentId")
    text: str


class TaskLogEvent(BaseModel):
    """WebSocket event: new log entry."""

    type: Literal["task.log"] = "task.log"
    entry: LogEntry


# --- Memory Models ---

class MemoryRecord(BaseModel):
    """Memory record for long-term storage."""

    id: str
    summary: str
    kind: Literal["outcome", "lesson"]
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class MemoryWriteEvent(BaseModel):
    """WebSocket event: memory record written."""

    type: Literal["memory.write"] = "memory.write"
    record: MemoryRecord


# --- Eval Models ---

class EvalRun(BaseModel):
    """Evaluation run result."""

    id: str
    label: str
    value: float
    unit: str
    delta: float


class EvalResultEvent(BaseModel):
    """WebSocket event: eval result broadcast."""

    type: Literal["eval.result"] = "eval.result"
    run: EvalRun


# --- Request Models ---

class PlanRequest(BaseModel):
    """POST /api/tasks/plan request body."""

    goal: str = Field(..., min_length=1, max_length=2000)


# --- WebSocket wrapper ---

class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper."""

    type: str
    data: dict
