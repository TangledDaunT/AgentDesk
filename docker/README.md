# Docker

Container orchestration for AgentDesk deployment.

## Planned Services

| Service | Image | Purpose |
|---------|-------|---------|
| frontend | Node:20-alpine | React dashboard |
| backend | Python:3.11-slim | FastAPI orchestration |
| postgres | postgres:16 | Relational data |
| qdrant | qdrant/qdrant:latest | Vector store |
| redis | redis:7-alpine | Task queue, pub/sub |
| nginx | nginx:alpine | Reverse proxy |

## Architecture

```
                    nginx
                      |
        +-------------+-------------+
        |                           |
    frontend                   backend (FastAPI)
        |                           |
        +-------------+-------------+
                      |
        +-------------+-------------+
        |             |             |
    postgres      qdrant         redis
```

## Volumes

- `postgres_data` → Persistent relational data
- `qdrant_storage` → Vector embeddings
- `redis_data` → Session persistence
- `logs` → Aggregated logs

## Networks

- `agentdesk-internal` → Service-to-service
- `agentdesk-public` → External-facing
