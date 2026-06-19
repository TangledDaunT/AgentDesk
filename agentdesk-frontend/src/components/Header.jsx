import React, { useState } from 'react'
import { useAgentStore } from '../store/agentStore'

export default function Header() {
  const connected = useAgentStore((s) => s.connected)
  const submitGoal = useAgentStore((s) => s.submitGoal)
  const [goal, setGoal] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!goal.trim()) return
    submitGoal(goal.trim())
    setGoal('')
  }

  return (
    <header className="flex items-center justify-between gap-6 px-6 py-4 border-b border-void-line bg-void-surface/80 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-signal/10 border border-signal/30 flex items-center justify-center">
          <i className="ti ti-hierarchy-3 text-signal text-base" aria-hidden="true"></i>
        </div>
        <div>
          <h1 className="text-[15px] font-medium text-slate-text leading-none">AgentDesk</h1>
          <p className="text-[11px] text-slate-faint mt-0.5">multi-agent orchestration</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 max-w-xl">
        <div className="relative">
          <i
            className="ti ti-terminal-2 absolute left-3 top-1/2 -translate-y-1/2 text-slate-faint text-sm"
            aria-hidden="true"
          ></i>
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="give the planner a goal..."
            className="w-full bg-void border border-void-line rounded-md py-2 pl-9 pr-3 text-[13px] text-slate-text placeholder:text-slate-faint focus:border-signal/40 focus:outline-none transition-colors"
          />
        </div>
      </form>

      <div className="flex items-center gap-2 text-[11px] text-slate-muted">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            connected ? 'bg-signal animate-pulse-slow' : 'bg-danger'
          }`}
        ></span>
        {connected ? 'connected' : 'offline — showing demo data'}
      </div>
    </header>
  )
}
