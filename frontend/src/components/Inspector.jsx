import React from 'react'
import { useAgentStore, AGENT_STATUS } from '../store/agentStore'

const STATUS_LABEL = {
  [AGENT_STATUS.IDLE]: 'idle',
  [AGENT_STATUS.THINKING]: 'thinking',
  [AGENT_STATUS.ACTIVE]: 'active',
  [AGENT_STATUS.ERROR]: 'error'
}

const STATUS_COLOR_CLASS = {
  [AGENT_STATUS.IDLE]: 'text-slate-muted',
  [AGENT_STATUS.THINKING]: 'text-amber',
  [AGENT_STATUS.ACTIVE]: 'text-signal',
  [AGENT_STATUS.ERROR]: 'text-danger'
}

function AgentDetail({ agent, tasks }) {
  const relatedTask = tasks.find((t) => t.id === agent.currentTask)

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-[14px] font-medium text-slate-text">{agent.name}</h3>
          <span className={`text-[11px] ${STATUS_COLOR_CLASS[agent.status]}`}>
            {STATUS_LABEL[agent.status]}
          </span>
        </div>
        <p className="text-[12px] text-slate-muted mt-1 leading-relaxed">{agent.description}</p>
      </div>

      <div>
        <p className="text-[10px] text-slate-faint uppercase tracking-wide mb-1.5">Tools</p>
        <div className="flex flex-wrap gap-1.5">
          {agent.toolsUsed.map((tool) => (
            <span
              key={tool}
              className="text-[10.5px] px-2 py-1 rounded bg-void-raised border border-void-line text-violet"
            >
              {tool}
            </span>
          ))}
        </div>
      </div>

      {relatedTask && (
        <div>
          <p className="text-[10px] text-slate-faint uppercase tracking-wide mb-1.5">
            Current task
          </p>
          <p className="text-[12px] text-slate-text leading-snug">{relatedTask.goal}</p>
        </div>
      )}
    </div>
  )
}

function TaskDetail({ task, agent }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-[14px] font-medium text-slate-text leading-snug">{task.goal}</h3>
        <p className="text-[11px] text-slate-faint mt-1">
          assigned to {agent ? agent.name : 'unassigned'}
        </p>
      </div>
      <div>
        <p className="text-[10px] text-slate-faint uppercase tracking-wide mb-1.5">Progress</p>
        <div className="h-1.5 bg-void-line rounded-full overflow-hidden">
          <div
            className="h-full bg-signal/70 rounded-full"
            style={{ width: `${task.progress}%` }}
          ></div>
        </div>
        <p className="text-[11px] text-slate-muted mt-1">{task.progress}%</p>
      </div>
      <div>
        <p className="text-[10px] text-slate-faint uppercase tracking-wide mb-1.5">Started</p>
        <p className="text-[12px] text-slate-muted">
          {new Date(task.startedAt).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}

export default function Inspector() {
  const agents = useAgentStore((s) => s.agents)
  const tasks = useAgentStore((s) => s.tasks)
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId)
  const selectedTaskId = useAgentStore((s) => s.selectedTaskId)

  const selectedAgent = agents.find((a) => a.id === selectedAgentId)
  const selectedTask = tasks.find((t) => t.id === selectedTaskId)
  const taskAgent = selectedTask
    ? agents.find((a) => a.id === selectedTask.assignedAgentId)
    : null

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2.5 border-b border-void-line">
        <h2 className="text-[11px] font-medium text-slate-muted tracking-wide uppercase">
          Inspector
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {selectedAgent && <AgentDetail agent={selectedAgent} tasks={tasks} />}
        {selectedTask && <TaskDetail task={selectedTask} agent={taskAgent} />}
        {!selectedAgent && !selectedTask && (
          <div className="h-full flex flex-col items-center justify-center text-center py-8">
            <i className="ti ti-pointer text-slate-faint text-xl mb-2" aria-hidden="true"></i>
            <p className="text-[11.5px] text-slate-faint">
              select a node or task to inspect
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
