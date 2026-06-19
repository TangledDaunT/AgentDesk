import React, { useEffect, useRef } from 'react'
import { useAgentStore } from '../store/agentStore'

export default function LogFeed() {
  const logs = useAgentStore((s) => s.logs)
  const agents = useAgentStore((s) => s.agents)
  const scrollRef = useRef(null)

  const agentById = Object.fromEntries(agents.map((a) => [a.id, a]))

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs.length])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-void-line">
        <h2 className="text-[11px] font-medium text-slate-muted tracking-wide uppercase">
          Activity log
        </h2>
        <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse-slow"></span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        {[...logs].reverse().map((log) => {
          const agent = agentById[log.agentId]
          return (
            <div key={log.id} className="flex items-start gap-2 text-[11.5px] leading-snug">
              <span className="text-slate-faint shrink-0 tabular-nums">{log.ts}</span>
              <span className="text-violet shrink-0">{agent ? agent.name : log.agentId}</span>
              <span className="text-slate-muted">{log.text}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
