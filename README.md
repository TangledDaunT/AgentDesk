# AgentDesk

A self-hosted multi-agent orchestration platform with MCP tool-calling and persistent memory.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Anthropic API key

### 1. Clone and setup

```bash
git clone https://github.com/TangledDaunT/AgentDesk.git
cd AgentDesk

# Setup backend
cd backend
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# Install Python dependencies
pip install -r requirements.txt

cd ..
```

### 2. Start infrastructure (Redis + Qdrant)

```bash
docker-compose up -d redis qdrant
```

### 3. Seed Qdrant with sample documents

```bash
cd backend
python scripts/seed_qdrant.py
cd ..
```

### 4. Start backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Start frontend (new terminal)

```bash
cd frontend
npm install  # first time only
npm run dev
```

### 6. Access

- Dashboard: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Full Docker deployment

```bash
# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your ANTHROPIC_API_KEY

# Start all services
docker-compose up -d

# Seed data
docker-compose exec backend python scripts/seed_qdrant.py
```

## Project Structure

```
AgentDesk/
├── frontend/          # React + Vite dashboard
│   ├── src/
│   │   ├── components/    # UI components (3D graph, task queue, etc.)
│   │   ├── store/         # Zustand state + WebSocket handling
│   │   └── App.jsx        # Main app component
│   └── package.json
│
├── backend/           # FastAPI + LangGraph orchestration
│   ├── agents/        # Planner, Research, Code, Data agents
│   ├── tools/         # Web search, filesystem, Qdrant tools
│   ├── memory/        # Long-term memory with Qdrant
│   ├── websocket/     # WebSocket manager with Redis pub/sub
│   ├── eval/          # Evaluation harness + 18 benchmarks
│   ├── scripts/       # seed_qdrant.py, run_eval.py
│   ├── main.py        # FastAPI app
│   └── Dockerfile
│
├── database/          # Schema documentation
├── memory/            # Memory architecture docs
├── redis/             # Redis config docs
├── docker/            # Deployment docs
├── docker-compose.yml # Full stack orchestration
└── ARCHITECTURE.md    # System design docs
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | Get all 4 agent states |
| `/api/tasks` | GET | Get all tasks (recent first) |
| `/api/tasks/plan` | POST | Submit goal → planner decomposes → executes |
| `/api/memory` | GET | Get recent memory records |
| `/api/eval/run` | POST | Run 18 benchmark tests |
| `/api/stats` | GET | System stats |
| `/ws/orchestrator` | WS | Real-time events |

## WebSocket Events

Frontend receives live updates via WebSocket:

- `agent.status` — Agent state changed (idle/thinking/active/error)
- `task.created` — New task created
- `task.updated` — Task progress updated
- `task.log` — Activity log entry
- `memory.write` — New memory stored in Qdrant
- `eval.result` — Benchmark completed

## Running Evaluations

```bash
# Standalone script
cd backend
python scripts/run_eval.py

# Or via API (updates live in UI)
curl -X POST http://localhost:8000/api/eval/run
```

Results are saved to `backend/eval_results.json`.

## Architecture Overview

```
User Goal
    ↓
[Planner Agent] LangGraph workflow
    ↓
Decomposes into 2-4 subtasks
    ↓
[Research] ← web_search, web_fetch
[Code]     ← fs_read, fs_write, shell
[Data]     ← qdrant_query
    ↓
Results stored in Qdrant (long-term memory)
    ↓
Real-time updates via WebSocket to React dashboard
```

## Agents

### Planner
- Decomposes user goals into subtasks
- Uses LangGraph for workflow orchestration
- Coordinates Research, Code, and Data agents

### Research
- Web search via DuckDuckGo (or SerpAPI)
- Fetches and extracts webpage content
- Synthesizes findings

### Code
- Reads/writes files in sandboxed workspace
- Executes Python/shell commands
- Generates and tests code

### Data
- Queries Qdrant vector database
- Semantic similarity search
- Retrieves relevant past outcomes

## Memory Layer

**Short-term**: Redis stores conversation buffers
**Long-term**: Qdrant stores embeddings of:
- Task outcomes
- Lessons learned
- Reusable patterns

After each task, the outcome is embedded and stored. Future tasks retrieve similar past outcomes via RAG.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite 6, Tailwind CSS, Three.js, Zustand |
| Backend | FastAPI, LangGraph, LangChain |
| LLM | Claude Sonnet 4.6 via Anthropic API |
| Vector Store | Qdrant |
| Task Queue | Redis |
| Database | SQLite (async) |
| Tools | DuckDuckGo search, Filesystem, Qdrant |
| Deployment | Docker Compose |

## License

MIT
