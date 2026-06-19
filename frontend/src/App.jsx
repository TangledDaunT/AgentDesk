import React, { useEffect } from 'react'
import Header from './components/Header.jsx'
import AgentGraph3D from './components/AgentGraph3D.jsx'
import TaskQueue from './components/TaskQueue.jsx'
import Inspector from './components/Inspector.jsx'
import MemoryFeed from './components/MemoryFeed.jsx'
import LogFeed from './components/LogFeed.jsx'
import EvalStrip from './components/EvalStrip.jsx'
import { useAgentStore } from './store/agentStore'
import { mockAgents, mockTasks, mockMemoryRecords, mockEvalRuns, mockLogs } from './store/mockData.js'
import { useMockLiveUpdates } from './hooks/useMockLiveUpdates.js'

export default function App() {
  const hydrate = useAgentStore((s) => s.hydrate)
  const setConnected = useAgentStore((s) => s.setConnected)

  useEffect(() => {
    // Claude Code: replace this block with real fetches to
    // GET /api/agents and GET /api/tasks, then setConnected(true)
    // once the WebSocket handshake succeeds.
    hydrate({
      agents: mockAgents,
      tasks: mockTasks,
      memoryRecords: mockMemoryRecords,
      evalRuns: mockEvalRuns,
      logs: mockLogs
    })
    setConnected(false)
  }, [hydrate, setConnected])

  useMockLiveUpdates(true)

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <Header />

      <main className="flex-1 grid grid-cols-[260px_1fr_300px] gap-px bg-void-line overflow-hidden">
        <aside className="bg-void-surface overflow-hidden">
          <TaskQueue />
        </aside>

        <section className="bg-void relative overflow-hidden flex flex-col">
          <div className="flex-1 relative grid-bg">
            <AgentGraph3D />
          </div>
          <div className="border-t border-void-line p-3">
            <EvalStrip />
          </div>
        </section>

        <aside className="bg-void-surface flex flex-col overflow-hidden">
          <div className="flex-[1.1] overflow-hidden border-b border-void-line">
            <Inspector />
          </div>
          <div className="flex-1 overflow-hidden border-b border-void-line">
            <MemoryFeed />
          </div>
          <div className="flex-1 overflow-hidden">
            <LogFeed />
          </div>
        </aside>
      </main>
    </div>
  )
}
