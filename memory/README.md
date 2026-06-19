# Memory Layer

Persistent context across agent sessions.

## Architecture

### Short-Term Memory (Conversation Buffer)
- Redis-backed session storage
- Context window management
- Per-session agent state

### Long-Term Memory (Vector Store)
- Qdrant for semantic retrieval
- Task outcome embeddings
- Reusable solution patterns
- RAG-enabled recall

### Memory Types

| Type | Store | Use Case |
|------|-------|----------|
| Ephemeral | Redis | Current conversation context |
| Working | Redis | Active task state |
| Semantic | Qdrant | Past task embeddings |
| Procedural | PostgreSQL | Agent behavior patterns |

## RAG Pipeline

1. Embed task description
2. Retrieve similar past tasks from Qdrant
3. Inject relevant context into planner prompt
4. Store outcome embedding after completion
