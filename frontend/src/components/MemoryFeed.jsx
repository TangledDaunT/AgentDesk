import React from 'react'
import { useAgentStore } from '../store/agentStore'

const KIND_ICON = {
  outcome: 'ti-circle-check',
  lesson: 'ti-bulb'
}

const KIND_COLOR = {
  outcome: 'text-signal',
  lesson: 'text-amber'
}

export default function MemoryFeed() {
  const records = useAgentStore((s) => s.memoryRecords)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-void-line">
        <i className="ti ti-database text-violet text-[13px]" aria-hidden="true"></i>
        <h2 className="text-[11px] font-medium text-slate-muted tracking-wide uppercase">
          Memory
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {records.map((record) => (
          <div key={record.id} className="flex items-start gap-2">
            <i
              className={`ti ${KIND_ICON[record.kind] ?? 'ti-circle'} ${KIND_COLOR[record.kind]} text-[13px] mt-0.5 shrink-0`}
              aria-hidden="true"
            ></i>
            <p className="text-[11.5px] text-slate-muted leading-snug">{record.summary}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
