# AgentDesk — frontend

A control-room UI for the AgentDesk multi-agent orchestration platform: a live 3D
graph of agents (planner + specialists), a task queue, a memory feed, and an
eval metrics strip.

This frontend is fully functional standalone on mock data (see
`src/store/mockData.js`). It is built to be wired to a FastAPI backend.

## Stack

- React 18 + Vite
- Tailwind CSS (design tokens in `tailwind.config.js`)
- `@react-three/fiber` + `@react-three/drei` for the 3D agent graph
- `zustand` for state (single store in `src/store/agentStore.js`)
- Tabler icons via CDN, Space Grotesk + JetBrains Mono via Google Fonts

## Run it

```bash
npm install
npm run dev
```

Opens on `http://localhost:5173`. The Vite dev server proxies `/api` and `/ws`
to `http://localhost:8000` (see `vite.config.js`) — point this at wherever
the FastAPI backend runs.

## What's already built (don't rebuild these)

- `src/components/AgentGraph3D.jsx` — the 3D graph. Agent nodes are
  icosahedrons that pulse when `status` is `active`/`thinking`, with particle
  flow from the planner node to whichever agent is currently `active`.
- `src/components/TaskQueue.jsx`, `Inspector.jsx`, `MemoryFeed.jsx`,
  `LogFeed.jsx`, `EvalStrip.jsx`, `Header.jsx` — all the surrounding panels.
- `src/store/agentStore.js` — the single source of truth. All components
  read from this store; none of them know about HTTP or WebSockets directly.

## Integration checklist for the backend

The store already defines the event contract. Implement these on the FastAPI
side and wire them in per the `BACKEND INTEGRATION NOTES` comment at the top
of `src/store/agentStore.js`:

1. **`GET /api/agents`** → returns `Agent[]`
   ```ts
   { id, name, role, status: "idle"|"thinking"|"active"|"error",
     currentTask: string|null, description, toolsUsed: string[],
     position: [x, y, z] }
   ```
   `position` is the 3D layout coordinate — keep the planner near `[0, 1.6, 0]`
   and specialists arranged around it, or compute a force-directed layout
   server-side and send updated positions over the socket.

2. **`GET /api/tasks`** → returns `Task[]`
   ```ts
   { id, goal, assignedAgentId, status: "queued"|"planning"|"running"|"done"|"failed",
     progress: number (0-100), startedAt: ISO string, parentTaskId: string|null }
   ```

3. **`POST /api/tasks/plan`** body `{ goal: string }` — triggers the planner
   agent to decompose the goal and create subtasks. Wire this into
   `submitGoal` in `agentStore.js`.

4. **`WS /ws/orchestrator`** — streams events matching `applyServerEvent`'s
   switch cases in `agentStore.js`:
   ```ts
   { type: "agent.status", agentId, status, currentTask }
   { type: "task.created", task: Task }
   { type: "task.updated", taskId, patch: Partial<Task> }
   { type: "task.log", entry: { id, ts, agentId, text } }
   { type: "memory.write", record: { id, summary, kind: "outcome"|"lesson", createdAt } }
   { type: "eval.result", run: { id, label, value, unit, delta } }
   ```

5. Create `src/lib/socket.js` that opens the WebSocket on app mount, calls
   `useAgentStore.getState().applyServerEvent(JSON.parse(event.data))` on
   each message, and calls `setConnected(true/false)` on open/close.

6. Once the socket is wired, delete `src/hooks/useMockLiveUpdates.js` and its
   usage in `App.jsx` — it only exists to animate progress bars in demo mode.

7. Replace the `hydrate(...)` call with mock data in `App.jsx`'s `useEffect`
   with real fetches to `/api/agents` and `/api/tasks`.

## Design tokens

Colors, fonts, and animation timings are defined in `tailwind.config.js`.
Status color mapping (keep consistent if adding new agent states):
- idle → slate (`#475569`)
- thinking → amber (`#F5A623`)
- active → signal/cyan (`#5EEAD4`)
- error → danger/red (`#F0654A`)
