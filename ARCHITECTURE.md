# AgentDesk Architecture

Multi-agent orchestration platform with MCP tool-calling and persistent memory.

## Overview

AgentDesk is a self-hosted platform where a planner agent breaks down tasks, delegates to specialized sub-agents (each with MCP tool access), and a memory layer persists context across sessions.

## Directory Structure

```
AgentDesk/
├── frontend/          # React + Vite dashboard
├── backend/           # FastAPI + LangGraph orchestration
├── database/          # PostgreSQL + Qdrant schemas
├── memory/            # Short-term (Redis) + long-term (Qdrant) memory
├── redis/             # Task queue and pub/sub config
├── docker/            # Docker Compose orchestration
└── ARCHITECTURE.md    # This file
```

## Core Flow

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
[Memory Layer] Store Outcome → Qdrant
    ↓
[Frontend] Real-time Task Graph Visualization
```

## Key Components

### 1. Planner Agent
- LangGraph-based workflow orchestration
- Task decomposition and delegation
- Dynamic agent selection based on capabilities

### 2. Specialized Sub-Agents
- **Research Agent**: Web search, API calls via MCP
- **Code Agent**: File read/write, code execution via MCP
- **Data Agent**: Database queries, retrieval via MCP

### 3. Memory Layer
- **Short-term**: Redis for conversation buffers
- **Long-term**: Qdrant vector store for RAG
- **Procedural**: PostgreSQL for execution patterns

### 4. MCP Integration
- MCP servers for external tool access
- Tool registry and dynamic discovery
- Standardized tool-calling protocol

### 5. Evaluation Harness
- 15-20 benchmark tasks
- Success rate, latency, tool-call accuracy metrics
- Automated regression testing

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Vite, Tailwind CSS |
| Backend API | FastAPI |
| Agent Framework | LangChain, LangGraph |
| Vector Store | Qdrant |
| Task Queue | Redis + Celery |
| Database | PostgreSQL |
| Tool Protocol | MCP SDK |
| Deployment | Docker, Docker Compose |

## Design Principles

1. **Modularity**: Each agent is independently deployable
2. **Observability**: Full execution trace and metrics
3. **Extensibility**: Easy to add new MCP tools and agents
4. **Testability**: Comprehensive evaluation harness
