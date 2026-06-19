# Backend

FastAPI-based orchestration layer for AgentDesk.

## Planned Architecture

### Core Components

- **Planner Agent** (`agents/planner/`)
  - Takes user goals, breaks into subtasks
  - Uses LangGraph for workflow orchestration
  - Delegates to specialized sub-agents

- **Specialized Sub-Agents** (`agents/specialized/`)
  - Research Agent: Web search via MCP
  - Code Agent: File read/write via MCP
  - Data Agent: Database queries via MCP

- **MCP Tool Layer** (`mcp/`)
  - MCP server configurations
  - Tool registry and discovery
  - Integration with external services

- **API Layer** (`api/`)
  - REST endpoints for frontend
  - WebSocket for real-time updates
  - Task submission and monitoring

## Services

| Service | Purpose |
|---------|---------|
| Task Service | Queue and track task execution |
| Agent Service | Manage agent lifecycle |
| Memory Service | Short/long-term memory access |
| Evaluation Service | Benchmark harness and metrics |

## Stack

- FastAPI
- LangChain / LangGraph
- Redis (task queue, pub/sub)
- Qdrant (vector store for memory)
