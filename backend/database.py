"""Database layer for AgentDesk - SQLite with async support."""

import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime, select, func

from config import get_settings

settings = get_settings()

# Async SQLite engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for tasks."""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    goal = Column(String, nullable=False)
    assigned_agent_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    parent_task_id = Column(String, nullable=True)
    result = Column(String, nullable=True)  # JSON string of result/error

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "assignedAgentId": self.assigned_agent_id,
            "status": self.status,
            "progress": self.progress,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "parentTaskId": self.parent_task_id,
        }


class EvalResultModel(Base):
    """SQLAlchemy model for evaluation results."""

    __tablename__ = "eval_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_id = Column(String, nullable=False)
    goal = Column(String, nullable=False)
    success = Column(String, nullable=False)  # "passed" | "failed"
    latency_ms = Column(Float, nullable=False)
    tool_calls_correct = Column(Float, default=0.0)  # 0-1 accuracy
    agent_selected_correctly = Column(String, nullable=False)  # "yes" | "no"
    error_message = Column(String, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow)


@asynccontextmanager
async def get_db():
    """Get database session as async context manager."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --- Task CRUD operations ---

async def create_task(
    goal: str,
    assigned_agent_id: str,
    parent_task_id: Optional[str] = None,
    status: str = "queued",
) -> TaskModel:
    """Create a new task."""
    async with get_db() as session:
        task = TaskModel(
            id=str(uuid.uuid4()),
            goal=goal,
            assigned_agent_id=assigned_agent_id,
            status=status,
            parent_task_id=parent_task_id,
        )
        session.add(task)
        await session.flush()
        await session.refresh(task)
        return task


async def get_task(task_id: str) -> Optional[TaskModel]:
    """Get task by ID."""
    async with get_db() as session:
        result = await session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        return result.scalar_one_or_none()


async def update_task(
    task_id: str,
    status: Optional[str] = None,
    progress: Optional[float] = None,
    result: Optional[str] = None,
) -> Optional[TaskModel]:
    """Update task fields."""
    async with get_db() as session:
        task = await session.get(TaskModel, task_id)
        if not task:
            return None

        if status is not None:
            task.status = status
            if status in ("running", "planning") and not task.started_at:
                task.started_at = datetime.utcnow()
            if status in ("done", "failed"):
                task.completed_at = datetime.utcnow()

        if progress is not None:
            task.progress = progress

        if result is not None:
            task.result = result

        await session.flush()
        return task


async def get_all_tasks(limit: int = 100) -> List[TaskModel]:
    """Get all tasks, most recent first."""
    async with get_db() as session:
        result = await session.execute(
            select(TaskModel)
            .order_by(TaskModel.started_at.desc().nullslast())
            .limit(limit)
        )
        return result.scalars().all()


async def get_task_count_by_status() -> dict:
    """Get count of tasks grouped by status."""
    async with get_db() as session:
        result = await session.execute(
            select(TaskModel.status, func.count())
            .group_by(TaskModel.status)
        )
        return {row[0]: row[1] for row in result.all()}


# --- Eval operations ---

async def save_eval_result(
    benchmark_id: str,
    goal: str,
    success: bool,
    latency_ms: float,
    tool_calls_correct: float,
    agent_selected_correctly: bool,
    error_message: Optional[str] = None,
) -> EvalResultModel:
    """Save evaluation result to database."""
    async with get_db() as session:
        result = EvalResultModel(
            id=str(uuid.uuid4()),
            benchmark_id=benchmark_id,
            goal=goal,
            success="passed" if success else "failed",
            latency_ms=latency_ms,
            tool_calls_correct=tool_calls_correct,
            agent_selected_correctly="yes" if agent_selected_correctly else "no",
            error_message=error_message,
        )
        session.add(result)
        await session.flush()
        return result


async def get_eval_stats() -> dict:
    """Get aggregate evaluation statistics."""
    async with get_db() as session:
        total = await session.scalar(select(func.count()).select_from(EvalResultModel))
        passed = await session.scalar(
            select(func.count())
            .select_from(EvalResultModel)
            .where(EvalResultModel.success == "passed")
        )
        avg_latency = await session.scalar(
            select(func.avg(EvalResultModel.latency_ms)).select_from(EvalResultModel)
        )
        avg_accuracy = await session.scalar(
            select(func.avg(EvalResultModel.tool_calls_correct)).select_from(EvalResultModel)
        )

        return {
            "total": total or 0,
            "passed": passed or 0,
            "avg_latency_ms": round(avg_latency or 0, 2),
            "avg_tool_accuracy": round((avg_accuracy or 0) * 100, 1),
        }
