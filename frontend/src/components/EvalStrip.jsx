import React from 'react'
import { useAgentStore } from '../store/agentStore'

export default function EvalStrip() {
  const evalRuns = useAgentStore((s) => s.evalRuns)

  return (
    <div className="grid grid-cols-4 gap-px bg-void-line border border-void-line rounded-lg overflow-hidden">
      {evalRuns.map((run) => {
        const positive = run.delta >= 0
        return (
          <div key={run.id} className="bg-void-surface px-4 py-3">
            <p className="text-[10px] text-slate-faint uppercase tracking-wide truncate">
              {run.label}
            </p>
            <div className="flex items-baseline gap-1.5 mt-1">
              <span className="text-[20px] font-display font-medium text-slate-text">
                {run.value}
              </span>
              <span className="text-[11px] text-slate-faint">{run.unit}</span>
            </div>
            <div
              className={`flex items-center gap-0.5 text-[10.5px] mt-0.5 ${
                positive ? 'text-signal' : 'text-danger'
              }`}
            >
              <i
                className={`ti ${positive ? 'ti-trending-up' : 'ti-trending-down'} text-[12px]`}
                aria-hidden="true"
              ></i>
              {Math.abs(run.delta)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
