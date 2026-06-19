# AgentDesk

A self-hosted multi-agent orchestration platform with MCP tool-calling and persistent memory.

## Overview

AgentDesk enables autonomous task execution through a planner-subagent architecture:
- **Planner Agent**: Decomposes user goals into subtasks
- **Specialized Sub-Agents**: Research, code, and data retrieval agents with MCP tool access
- **Memory Layer**: Short-term (Redis) and long-term (Qdrant) context persistence
- **Real-time Dashboard**: React-based visualization of task graphs and agent states

## Quick Start

```bash
# Clone the repository
git clone https://github.com/TangledDaunT/AgentDesk.git
cd AgentDesk

# Start all services (planned)
docker-compose up -d

# Access dashboard
open http://localhost:5173
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `frontend/` | React + Vite dashboard |
| `backend/` | FastAPI + LangGraph orchestration |
| `database/` | PostgreSQL + Qdrant schemas |
| `memory/` | Short-term (Redis) + long-term (Qdrant) memory |
| `redis/` | Task queue and pub/sub configuration |
| `docker/` | Docker Compose orchestration |

## Core Architecture

```
User Request
    ↓
[Frontend] React Dashboard
    ↓
[Backend] Planner Agent (LangGraph)
    ↓
Decomposes into Subtasks
    ↓
[Sub-Agents] Research | Code | Data
    ↓
[MCP Tools] Web Search | File Ops | DB Queries
    ↓
[Memory] Store Outcome → Qdrant
    ↓
[Frontend] Real-time Task Graph
```

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Three.js (3D visualization)
- **Backend**: FastAPI, LangChain, LangGraph
- **Memory**: Qdrant (vector), Redis (session), PostgreSQL (relational)
- **Tools**: MCP SDK for external tool calling
- **Deployment**: Docker, Docker Compose

## Roadmap

- [x] Frontend dashboard with mock data
- [ ] FastAPI backend with LangGraph orchestration
- [ ] MCP tool integration (research, code, data agents)
- [ ] Redis task queue and pub/sub
- [ ] Qdrant vector store for long-term memory
- [ ] PostgreSQL for execution tracking
- [ ] Evaluation harness (15-20 benchmark tasks)
- [ ] Docker Compose deployment

## License

MIT
