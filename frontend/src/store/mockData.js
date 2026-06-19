import { AGENT_STATUS, TASK_STATUS } from './agentStore'

export const mockAgents = [
  {
    id: 'planner',
    name: 'Planner',
    role: 'planner',
    status: AGENT_STATUS.ACTIVE,
    currentTask: 'task-3',
    description: 'Decomposes goals into subtasks and routes them to specialists',
    toolsUsed: ['task-graph', 'router'],
    position: [0, 1.6, 0]
  },
  {
    id: 'research',
    name: 'Research agent',
    role: 'research',
    status: AGENT_STATUS.THINKING,
    currentTask: 'task-1',
    description: 'Web search and source synthesis via MCP',
    toolsUsed: ['web_search', 'web_fetch'],
    position: [-2.6, -0.6, 0.4]
  },
  {
    id: 'code',
    name: 'Code agent',
    role: 'code',
    status: AGENT_STATUS.IDLE,
    currentTask: null,
    description: 'Reads, writes, and tests code via MCP filesystem tools',
    toolsUsed: ['fs_read', 'fs_write', 'shell'],
    position: [0, -1.4, -0.6]
  },
  {
    id: 'data',
    name: 'Data agent',
    role: 'data',
    status: AGENT_STATUS.ACTIVE,
    currentTask: 'task-2',
    description: 'Queries Qdrant and Postgres for structured retrieval',
    toolsUsed: ['qdrant_query', 'sql_query'],
    position: [2.6, -0.6, 0.4]
  }
]

export const mockTasks = [
  {
    id: 'task-1',
    goal: 'Find recent benchmarks comparing vector DB latency at 5M+ doc scale',
    assignedAgentId: 'research',
    status: TASK_STATUS.RUNNING,
    progress: 62,
    startedAt: '2026-06-20T09:14:00Z',
    parentTaskId: null
  },
  {
    id: 'task-2',
    goal: 'Pull top-20 similar cases for query embedding from legal corpus',
    assignedAgentId: 'data',
    status: TASK_STATUS.RUNNING,
    progress: 88,
    startedAt: '2026-06-20T09:13:10Z',
    parentTaskId: null
  },
  {
    id: 'task-3',
    goal: 'Plan: summarize retrieval quality across last 20 benchmark runs',
    assignedAgentId: 'planner',
    status: TASK_STATUS.PLANNING,
    progress: 30,
    startedAt: '2026-06-20T09:15:02Z',
    parentTaskId: null
  },
  {
    id: 'task-4',
    goal: 'Write evaluation harness script for tool-call accuracy',
    assignedAgentId: 'code',
    status: TASK_STATUS.DONE,
    progress: 100,
    startedAt: '2026-06-20T08:58:00Z',
    parentTaskId: null
  },
  {
    id: 'task-5',
    goal: 'Fetch and parse Qdrant collection schema for memory store',
    assignedAgentId: 'data',
    status: TASK_STATUS.DONE,
    progress: 100,
    startedAt: '2026-06-20T08:51:00Z',
    parentTaskId: null
  }
]

export const mockMemoryRecords = [
  { id: 'm1', summary: 'Qdrant + Qwen embeddings hit 94% match accuracy on legal corpus', kind: 'outcome', createdAt: '2026-06-19T18:02:00Z' },
  { id: 'm2', summary: 'Web search agent times out above 8s on rate-limited sources', kind: 'lesson', createdAt: '2026-06-19T15:40:00Z' },
  { id: 'm3', summary: 'Redis caching cut RAG query latency from 1.1s to 400ms', kind: 'outcome', createdAt: '2026-06-18T11:22:00Z' }
]

export const mockEvalRuns = [
  { id: 'e1', label: 'Tool-call accuracy', value: 91, unit: '%', delta: 3 },
  { id: 'e2', label: 'Avg task latency', value: 2.4, unit: 's', delta: -0.3 },
  { id: 'e3', label: 'Tasks completed', value: 18, unit: '/20', delta: 1 },
  { id: 'e4', label: 'Memory recall hits', value: 12, unit: '', delta: 2 }
]

export const mockLogs = [
  { id: 'l1', ts: '09:15:41', agentId: 'planner', text: 'decomposed goal into 3 subtasks' },
  { id: 'l2', ts: '09:15:12', agentId: 'data', text: 'qdrant_query returned 20 results in 184ms' },
  { id: 'l3', ts: '09:14:55', agentId: 'research', text: 'web_search: "vector db latency benchmark 2026"' },
  { id: 'l4', ts: '09:14:30', agentId: 'code', text: 'eval harness run complete — 18/20 passed' }
]
