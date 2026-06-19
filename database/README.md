# Database

Persistent storage layer for AgentDesk.

## Planned Schema

### PostgreSQL (Relational Data)

```
tasks/
  - id, status, goal, created_at, completed_at
  - parent_task_id (for subtasks)
  - assigned_agent, execution_logs

agents/
  - id, name, type, capabilities, mcp_tools
  - status, last_active

executions/
  - id, task_id, agent_id
  - tool_calls, latency, success/failure
  - metrics (token_usage, cost)
```

### Qdrant (Vector Store)

```
collections/
  - long_term_memory: Past task outcomes, reusable solutions
  - agent_knowledge: Domain-specific embeddings
  - conversation_buffer: Session context
```

## Migrations

Planned: Alembic for PostgreSQL schema migrations
