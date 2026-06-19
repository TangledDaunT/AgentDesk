import React, { useEffect, useRef, useState } from 'react'
import Header from './components/Header.jsx'
import AgentGraph3D from './components/AgentGraph3D.jsx'
import TaskQueue from './components/TaskQueue.jsx'
import Inspector from './components/Inspector.jsx'
import MemoryFeed from './components/MemoryFeed.jsx'
import LogFeed from './components/LogFeed.jsx'
import EvalStrip from './components/EvalStrip.jsx'
import { useAgentStore } from './store/agentStore'

// Backend API URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const hydrate = useAgentStore((s) => s.hydrate)
  const setConnected = useAgentStore((s) => s.setConnected)
  const applyServerEvent = useAgentStore((s) => s.applyServerEvent)
  const [error, setError] = useState(null)

  const wsRef = useRef(null)

  useEffect(() => {
    // Fetch initial data from backend
    const fetchInitialData = async () => {
      try {
        // Fetch agents
        const agentsRes = await fetch(`${API_URL}/api/agents`)
        const agents = await agentsRes.json()

        // Fetch tasks
        const tasksRes = await fetch(`${API_URL}/api/tasks`)
        const tasks = await tasksRes.json()

        // Fetch memory records
        const memoryRes = await fetch(`${API_URL}/api/memory`)
        const memoryRecords = await memoryRes.json()

        // Hydrate store with real data
        hydrate({
          agents,
          tasks,
          memoryRecords,
          evalRuns: [],
          logs: [],
        })

        setError(null)
      } catch (err) {
        console.error('Failed to fetch initial data:', err)
        setError('Backend connection failed. Ensure API is running on localhost:8000')
      }
    }

    // Connect WebSocket for live updates
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws/orchestrator`)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          applyServerEvent(data)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Attempt reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }

      ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        setConnected(false)
      }

      wsRef.current = ws
    }

    // Initialize
    fetchInitialData()
    connectWebSocket()

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [hydrate, setConnected, applyServerEvent])

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <Header />

      {error && (
        <div className="bg-red-900/50 text-red-200 px-4 py-2 text-sm border-b border-red-800">
          {error}
        </div>
      )}

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
          <Inspector />
          <div className="flex-1 border-t border-void-line overflow-hidden flex flex-col">
            <div className="h-1/2 border-b border-void-line overflow-hidden">
              <MemoryFeed />
            </div>
            <div className="h-1/2 overflow-hidden">
              <LogFeed />
            </div>
          </div>
        </aside>
      </main>
    </div>
  )
}
