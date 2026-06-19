# AgentDesk Backend

FastAPI + LangGraph orchestration layer for AgentDesk.

## Quick Start

### Prerequisites

- Python 3.11+
- Redis running (via Docker or local)
- Qdrant running (via Docker)
- Anthropic API key

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Start services (from project root)

```bash
# In one terminal
docker-compose up redis qdrant

# In another terminal (backend)
cd backend
uvicorn main:app --reload --port 8000

# In another terminal (frontend)
cd frontend
npm run dev
```

### 4. Access

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | Get all agent states |
| `/api/tasks` | GET | Get all tasks (recent first) |
| `/api/tasks/plan` | POST | Submit a goal for planning |
| `/api/memory` | GET | Get recent memory records |
| `/api/eval/run` | POST | Start evaluation harness |
| `/api/stats` | GET | System statistics |
| `/ws/orchestrator` | WS | Real-time event stream |
| `/health` | GET | Health check |

## WebSocket Events

The WebSocket broadcasts these event types:

- `agent.status` — Agent state changed
- `task.created` — New task created
- `task.updated` — Task progress/status update
- `task.log` — Activity log entry
- `memory.write` — New memory record stored
- `eval.result` — Evaluation benchmark result

## Scripts

```bash
# Seed Qdrant with sample documents
python scripts/seed_qdrant.py

# Run evaluation harness
python scripts/run_eval.py
```

## Architecture

### Agents

- **Planner** (`agents/planner.py`): Decomposes goals, coordinates sub-agents
- **Research** (`agents/research.py`): Web search via DuckDuckGo/SerpAPI
- **Code** (`agents/code.py`): File operations in sandboxed workspace
- **Data** (`agents/data.py`): Qdrant vector queries

### Memory Flow

1. Task completes → Outcome embedded
2. Stored in Qdrant with metadata
3. `memory.write` event broadcast
4. Future tasks retrieve similar past outcomes

### Evaluation

Benchmark harness runs 18 tasks across all agent types:
- Research: Web search accuracy
- Code: File operation success
- Data: Retrieval relevance
- Planner: End-to-end task completion

Metrics tracked:
- Success rate
- Tool-call accuracy
- Latency per task
- Agent selection correctness
