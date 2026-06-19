import React from 'react'
import { useAgentStore, TASK_STATUS } from '../store/agentStore'

const STATUS_STYLES = {
  [TASK_STATUS.QUEUED]: { label: 'queued', dot: 'bg-slate-idle', text: 'text-slate-muted' },
  [TASK_STATUS.PLANNING]: { label: 'planning', dot: 'bg-amber animate-pulse-fast', text: 'text-amber' },
  [TASK_STATUS.RUNNING]: { label: 'running', dot: 'bg-signal animate-pulse-fast', text: 'text-signal' },
  [TASK_STATUS.DONE]: { label: 'done', dot: 'bg-slate-idle', text: 'text-slate-muted' },
  [TASK_STATUS.FAILED]: { label: 'failed', dot: 'bg-danger', text: 'text-danger' }
}

function TaskRow({ task, agent, isSelected, onSelect }) {
  const style = STATUS_STYLES[task.status] ?? STATUS_STYLES[TASK_STATUS.QUEUED]

  return (
    <button
      onClick={() => onSelect(task.id)}
      className={`w-full text-left px-3 py-2.5 rounded-md border transition-colors ${
        isSelected
          ? 'border-signal/40 bg-signal/5'
          : 'border-transparent hover:border-void-line hover:bg-void-raised/60'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[12.5px] text-slate-text leading-snug line-clamp-2">{task.goal}</p>
        <span className={`shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full ${style.dot}`}></span>
      </div>
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-[10.5px] text-slate-faint">
          {agent ? agent.name : 'unassigned'}
        </span>
        <span className={`text-[10.5px] ${style.text}`}>{style.label}</span>
      </div>
      {task.status === TASK_STATUS.RUNNING && (
        <div className="mt-1.5 h-[3px] bg-void-line rounded-full overflow-hidden">
          <div
            className="h-full bg-signal/70 rounded-full transition-all"
            style={{ width: `${task.progress}%` }}
          ></div>
        </div>
      )}
    </button>
  )
}

export default function TaskQueue() {
  const tasks = useAgentStore((s) => s.tasks)
  const agents = useAgentStore((s) => s.agents)
  const selectedTaskId = useAgentStore((s) => s.selectedTaskId)
  const setSelectedTask = useAgentStore((s) => s.setSelectedTask)

  const agentById = Object.fromEntries(agents.map((a) => [a.id, a]))

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-void-line">
        <h2 className="text-[11px] font-medium text-slate-muted tracking-wide uppercase">
          Task queue
        </h2>
        <span className="text-[10.5px] text-slate-faint">{tasks.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto px-1.5 py-1.5 space-y-1">
        {tasks.map((task) => (
          <TaskRow
            key={task.id}
            task={task}
            agent={agentById[task.assignedAgentId]}
            isSelected={selectedTaskId === task.id}
            onSelect={setSelectedTask}
          />
        ))}
      </div>
    </div>
  )
}
