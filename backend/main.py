"""FastAPI backend for AgentDesk."""

import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import init_db, get_all_tasks, get_task_count_by_status
from models import (
    Agent,
    Task,
    MemoryRecord,
    EvalRun,
    PlanRequest,
)
from memory.qdrant_store import QdrantMemoryStore

settings = get_settings()

# Import agents (real or mock based on settings)
if settings.mock_mode:
    print("[MOCK MODE] Using mock agents (no API calls)")
    from agents.mock import MockPlannerAgent as PlannerAgent
    from agents.mock import MockResearchAgent as ResearchAgent
    from agents.mock import MockCodeAgent as CodeAgent
    from agents.mock import MockDataAgent as DataAgent
else:
    from agents.planner import PlannerAgent
    from agents.research import ResearchAgent
    from agents.code import CodeAgent
    from agents.data import DataAgent
from websocket.manager import (
    get_websocket_manager,
    broadcast_task_created,
    broadcast_eval_result,
)
from eval.harness import EvalHarness, BENCHMARKS
from eval.benchmarks import get_expected_agent

# Global state
agents: dict = {}
memory_store: QdrantMemoryStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global agents, memory_store

    # Startup: Initialize everything
    print("Initializing database...")
    await init_db()

    print("Initializing agents...")
    agents = {
        "planner": PlannerAgent(),
        "research": ResearchAgent(),
        "code": CodeAgent(),
        "data": DataAgent(),
    }

    print("Initializing memory store...")
    memory_store = QdrantMemoryStore()

    # Seed sample data if collection is empty
    try:
        memory_store.seed_sample_data()
    except Exception as e:
        print(f"Note: Could not seed sample data: {e}")

    # Start Redis listener in background
    print("Starting services...")
    ws_manager = get_websocket_manager()
    asyncio.create_task(ws_manager.start_redis_listener())

    print("AgentDesk backend ready!")
    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="AgentDesk API",
    description="Multi-agent orchestration platform backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Endpoints ---

@app.get("/api/agents")
async def get_agents() -> List[Agent]:
    """Get current state of all agents."""
    return [
        Agent(**agent.get_agent_info())
        for agent in agents.values()
    ]


@app.get("/api/tasks")
async def get_tasks(limit: int = 100) -> List[Task]:
    """Get all tasks, most recent first."""
    db_tasks = await get_all_tasks(limit)
    return [Task(**task.to_dict()) for task in db_tasks]


@app.post("/api/tasks/plan")
async def create_plan(request: PlanRequest):
    """Create a task plan from a goal."""
    planner = agents["planner"]

    # Create the parent task
    from database import create_task as db_create_task

    parent_task = await db_create_task(
        goal=request.goal,
        assigned_agent_id="planner",
        status="planning",
    )

    # Broadcast task created
    await broadcast_task_created({
        "id": parent_task.id,
        "goal": request.goal,
        "assignedAgentId": "planner",
        "status": "planning",
        "progress": 5,
        "parentTaskId": None,
    })

    # Kick off planning asynchronously
    asyncio.create_task(_run_planning(parent_task.id, request.goal))

    return {
        "success": True,
        "parentTaskId": parent_task.id,
        "message": "Planning started",
    }


async def _run_planning(task_id: str, goal: str):
    """Run planning in background."""
    try:
        await agents["planner"].execute(task_id, goal)
    except Exception as e:
        print(f"Planning failed: {e}")


@app.get("/api/memory")
async def get_memory(limit: int = 10) -> List[MemoryRecord]:
    """Get recent memory records."""
    records = await memory_store.get_recent(limit)
    return [MemoryRecord(**r) for r in records]


@app.post("/api/eval/run")
async def run_eval():
    """Start evaluation harness."""
    harness = EvalHarness(agents, memory_store)

    # Broadcast start
    await broadcast_eval_result(
        eval_id="eval-start",
        label="Eval Started",
        value=0,
        unit="tests",
        delta=0,
    )

    # Run in background
    asyncio.create_task(_run_evaluation(harness))

    return {"success": True, "message": "Evaluation started"}


async def _run_evaluation(harness: EvalHarness):
    """Run evaluation in background."""
    results = await harness.run_all()

    # Calculate aggregate metrics
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    avg_latency = sum(r["latency_ms"] for r in results) / total if total else 0
    avg_accuracy = sum(r["tool_calls_correct"] for r in results) / total if total else 0

    # Broadcast final results
    await broadcast_eval_result(
        eval_id=f"eval-{uuid.uuid4()}",
        label="Success Rate",
        value=round(passed / total * 100, 1) if total else 0,
        unit="%",
        delta=0,
    )
    await broadcast_eval_result(
        eval_id=f"eval-{uuid.uuid4()}",
        label="Avg Latency",
        value=round(avg_latency / 1000, 1),
        unit="s",
        delta=0,
    )
    await broadcast_eval_result(
        eval_id=f"eval-{uuid.uuid4()}",
        label="Tool Accuracy",
        value=round(avg_accuracy * 100, 1),
        unit="%",
        delta=0,
    )

    # Save results to file
    import json
    from pathlib import Path

    results_file = Path("eval_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "run_at": datetime.utcnow().isoformat(),
            "results": results,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "avg_latency_ms": avg_latency,
                "avg_tool_accuracy": avg_accuracy,
            }
        }, f, indent=2)

    print(f"Evaluation complete. Results saved to {results_file}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    task_counts = await get_task_count_by_status()

    return {
        "agents": len(agents),
        "tasks": task_counts,
        "status": "healthy",
    }


# --- WebSocket Endpoint ---

@app.websocket("/ws/orchestrator")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    manager = get_websocket_manager()
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive, handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle commands if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- Health Check ---

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
