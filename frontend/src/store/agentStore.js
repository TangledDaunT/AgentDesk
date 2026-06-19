import { create } from 'zustand'

/*
  BACKEND INTEGRATION NOTES FOR CLAUDE CODE
  ------------------------------------------
  This store currently runs on mock data (see mockData.js) so the UI is
  fully demoable without a backend. To wire it to the real FastAPI service:

  1. Replace `seedMockState()` call in App.jsx with a real fetch to
     GET /api/agents and GET /api/tasks on mount.

  2. Open a WebSocket to ws://<host>/ws/orchestrator and call
     applyServerEvent(event) on every message. Expected event shape:
       { type: 'agent.status', agentId, status, currentTask }
       { type: 'task.created', task }
       { type: 'task.updated', taskId, patch }
       { type: 'task.log', taskId, entry }
       { type: 'memory.write', record }
       { type: 'eval.result', run }

  3. submitGoal() should POST to /api/tasks/plan with { goal: string }
     instead of the local mock planner.

  All shapes below (Agent, Task, MemoryRecord, EvalRun) are the contract -
  keep field names stable so the components don't need to change.
*/

export const AGENT_STATUS = {
  IDLE: 'idle',
  THINKING: 'thinking',
  ACTIVE: 'active',
  ERROR: 'error'
}

export const TASK_STATUS = {
  QUEUED: 'queued',
  PLANNING: 'planning',
  RUNNING: 'running',
  DONE: 'done',
  FAILED: 'failed'
}

export const useAgentStore = create((set, get) => ({
  // --- connection state ---
  connected: false,
  setConnected: (connected) => set({ connected }),

  // --- core entities ---
  agents: [],
  tasks: [],
  memoryRecords: [],
  evalRuns: [],
  logs: [],

  selectedAgentId: null,
  selectedTaskId: null,

  setSelectedAgent: (id) => set({ selectedAgentId: id, selectedTaskId: null }),
  setSelectedTask: (id) => set({ selectedTaskId: id, selectedAgentId: null }),

  // --- bulk hydration (called on mount, replace with API fetch) ---
  hydrate: ({ agents, tasks, memoryRecords, evalRuns, logs }) =>
    set({ agents, tasks, memoryRecords, evalRuns, logs }),

  // --- mutators the WebSocket handler will call ---
  updateAgentStatus: (agentId, status, currentTask = null) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === agentId ? { ...a, status, currentTask } : a
      )
    })),

  addTask: (task) =>
    set((state) => ({ tasks: [task, ...state.tasks] })),

  updateTask: (taskId, patch) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, ...patch } : t))
    })),

  appendLog: (entry) =>
    set((state) => ({ logs: [...state.logs.slice(-199), entry] })),

  addMemoryRecord: (record) =>
    set((state) => ({ memoryRecords: [record, ...state.memoryRecords] })),

  addEvalRun: (run) =>
    set((state) => ({ evalRuns: [run, ...state.evalRuns] })),

  // --- single dispatcher for incoming WS events (wire this up in Claude Code) ---
  applyServerEvent: (event) => {
    const { type } = event
    switch (type) {
      case 'agent.status':
        get().updateAgentStatus(event.agentId, event.status, event.currentTask)
        break
      case 'task.created':
        get().addTask(event.task)
        break
      case 'task.updated':
        get().updateTask(event.taskId, event.patch)
        break
      case 'task.log':
        get().appendLog(event.entry)
        break
      case 'memory.write':
        get().addMemoryRecord(event.record)
        break
      case 'eval.result':
        get().addEvalRun(event.run)
        break
      default:
        console.warn('unhandled server event', type)
    }
  },

  // --- goal submission (replace body with real POST /api/tasks/plan) ---
  submitGoal: async (goalText) => {
    console.log('submitGoal called with', goalText, '- wire this to POST /api/tasks/plan')
  }
}))
