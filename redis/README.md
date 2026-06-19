# Redis

Task queue and pub/sub messaging for AgentDesk.

## Planned Usage

### Task Queue (Celery-compatible)
- Queue: `agentdesk:tasks`
- Priority levels: high, normal, low
- Retry logic with exponential backoff

### Pub/Sub Channels
- `agentdesk:events` → Task state changes
- `agentdesk:logs` → Real-time execution logs
- `agentdesk:metrics` → Performance metrics

### Session Storage
- Conversation buffers
- Agent state snapshots
- Rate limiting counters

## Configuration

```yaml
redis:
  host: redis
  port: 6379
  db: 0
  task_queue: agentdesk:tasks
  event_channel: agentdesk:events
```
