"""WebSocket connection manager with Redis pub/sub support."""

import json
import asyncio
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket
import redis.asyncio as redis

from config import get_settings

settings = get_settings()


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.redis_client: redis.Redis | None = None
        self._pubsub_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        # Send to all WebSocket connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

        # Also publish to Redis for multi-instance scenarios
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "agentdesk:events",
                    json.dumps(message),
                )
            except Exception:
                pass

    async def start_redis_listener(self):
        """Start listening to Redis pub/sub for inter-process events."""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("agentdesk:events")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # Broadcast to local WebSocket clients
                    await self._broadcast_to_locals(data)

        except Exception as e:
            print(f"Redis listener error: {e}")

    async def _broadcast_to_locals(self, message: Dict[str, Any]):
        """Broadcast only to local WebSocket clients (from Redis)."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.active_connections.discard(conn)


# Global manager instance
_websocket_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


# --- Event broadcasting helpers ---

async def broadcast_agent_status(
    agent_id: str,
    status: str,
    current_task: str | None = None,
):
    """Broadcast agent status change."""
    manager = get_websocket_manager()
    await manager.broadcast({
        "type": "agent.status",
        "agentId": agent_id,
        "status": status,
        "currentTask": current_task,
    })


async def broadcast_task_created(task: Dict[str, Any]):
    """Broadcast new task creation."""
    manager = get_websocket_manager()
    await manager.broadcast({
        "type": "task.created",
        "task": task,
    })


async def broadcast_task_updated(task_id: str, patch: Dict[str, Any]):
    """Broadcast task update."""
    manager = get_websocket_manager()
    await manager.broadcast({
        "type": "task.updated",
        "taskId": task_id,
        "patch": patch,
    })


async def broadcast_log(agent_id: str, text: str):
    """Broadcast activity log entry."""
    manager = get_websocket_manager()
    ts = datetime.now().strftime("%H:%M:%S")
    log_id = f"l{datetime.now().timestamp():.0f}"

    await manager.broadcast({
        "type": "task.log",
        "entry": {
            "id": log_id,
            "ts": ts,
            "agentId": agent_id,
            "text": text,
        },
    })


async def broadcast_memory_write(
    memory_id: str,
    summary: str,
    kind: str = "outcome",
):
    """Broadcast memory write event."""
    manager = get_websocket_manager()
    await manager.broadcast({
        "type": "memory.write",
        "record": {
            "id": memory_id,
            "summary": summary,
            "kind": kind,
            "createdAt": datetime.utcnow().isoformat(),
        },
    })


async def broadcast_eval_result(
    eval_id: str,
    label: str,
    value: float,
    unit: str,
    delta: float = 0.0,
):
    """Broadcast evaluation result."""
    manager = get_websocket_manager()
    await manager.broadcast({
        "type": "eval.result",
        "run": {
            "id": eval_id,
            "label": label,
            "value": value,
            "unit": unit,
            "delta": delta,
        },
    })
