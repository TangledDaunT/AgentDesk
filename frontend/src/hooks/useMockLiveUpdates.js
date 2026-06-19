import { useEffect } from 'react'
import { useAgentStore, AGENT_STATUS, TASK_STATUS } from '../store/agentStore'

/*
  Simulates WS events for demo purposes. Claude Code: delete this file and
  its usage in App.jsx once the real WebSocket connection in
  src/lib/socket.js (to be created) is wired to applyServerEvent().
*/
export function useMockLiveUpdates(enabled) {
  const updateTask = useAgentStore((s) => s.updateTask)
  const updateAgentStatus = useAgentStore((s) => s.updateAgentStatus)
  const appendLog = useAgentStore((s) => s.appendLog)
  const tasks = useAgentStore((s) => s.tasks)
  const agents = useAgentStore((s) => s.agents)

  useEffect(() => {
    if (!enabled) return

    const interval = setInterval(() => {
      const runningTasks = tasks.filter((t) => t.status === TASK_STATUS.RUNNING)
      if (runningTasks.length === 0) return

      const target = runningTasks[Math.floor(Math.random() * runningTasks.length)]
      const nextProgress = Math.min(100, target.progress + Math.ceil(Math.random() * 10))

      if (nextProgress >= 100) {
        updateTask(target.id, { progress: 100, status: TASK_STATUS.DONE })
        updateAgentStatus(target.assignedAgentId, AGENT_STATUS.IDLE, null)
        appendLog({
          id: `log-${Date.now()}`,
          ts: new Date().toLocaleTimeString('en-GB', { hour12: false }).slice(0, 8),
          agentId: target.assignedAgentId,
          text: 'task completed'
        })
      } else {
        updateTask(target.id, { progress: nextProgress })
      }
    }, 2200)

    return () => clearInterval(interval)
  }, [enabled, tasks, agents, updateTask, updateAgentStatus, appendLog])
}
