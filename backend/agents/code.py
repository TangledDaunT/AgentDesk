"""Code agent with filesystem tool access."""

from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from agents.base import BaseAgent
from tools.filesystem import read_file, write_file, list_files, execute_shell


class CodeState(TypedDict):
    """State for code agent."""
    task_id: str
    goal: str
    files_read: list
    files_written: list
    shell_output: str
    code_result: str
    status: str
    progress: float


class CodeAgent(BaseAgent):
    """Agent that performs code operations."""

    def __init__(self):
        super().__init__(
            agent_id="code",
            name="Code agent",
            role="code",
            description="Reads, writes, and tests code via MCP filesystem tools",
        )

        self.tools = ["fs_read", "fs_write", "shell"]

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        builder = StateGraph(CodeState)

        builder.add_node("analyze", self._analyze_node)
        builder.add_node("read_files", self._read_files_node)
        builder.add_node("write_files", self._write_files_node)
        builder.add_node("execute", self._execute_node)
        builder.add_node("finalize", self._finalize_node)

        builder.set_entry_point("analyze")
        builder.add_edge("analyze", "read_files")
        builder.add_conditional_edges(
            "read_files",
            self._should_write,
            {"write": "write_files", "execute": "execute"},
        )
        builder.add_conditional_edges(
            "write_files",
            self._should_execute,
            {"execute": "execute", "finalize": "finalize"},
        )
        builder.add_edge("execute", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile()

    def _should_write(self, state: CodeState) -> str:
        """Determine if we need to write files."""
        return "write" if state.get("files_written") else "execute"

    def _should_execute(self, state: CodeState) -> str:
        """Determine if we should execute commands."""
        return "execute" if "run" in state["goal"].lower() or "test" in state["goal"].lower() else "finalize"

    async def _analyze_node(self, state: CodeState) -> CodeState:
        """Analyze the coding task."""
        await self.set_status("thinking", state["task_id"])
        await self.update_task_progress(state["task_id"], "running", 10)
        await self.log(f"Analyzing: {state['goal'][:60]}...")

        # Determine if we need to read existing files
        prompt = f"""Given this task: {state['goal']}

What files should be read (if any)? What files should be created or modified?
Output as:
READ: [file1, file2]
WRITE: [file3, file4]
Or
CREATE: brief description of what to create"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["analysis"] = response.content

        return {**state, "progress": 20}

    async def _read_files_node(self, state: CodeState) -> CodeState:
        """Read requested files."""
        await self.log("Reading existing files...")

        files_read = []
        # Extract file names from goal (simple heuristic)
        if "read" in state["goal"].lower() or "update" in state["goal"].lower():
            # List files in workspace
            try:
                files = await list_files(".")
                files_read = files[:5]  # Read up to 5 recent files
                await self.log(f"Listed {len(files)} files in workspace")
            except Exception as e:
                await self.log(f"No files to read: {e}")

        await self.update_task_progress(state["task_id"], "running", 40)
        return {**state, "files_read": files_read, "progress": 40}

    async def _write_files_node(self, state: CodeState) -> CodeState:
        """Write generated code/files."""
        await self.set_status("active", state["task_id"])
        await self.log("Writing code/files...")

        # Generate code based on goal
        prompt = f"""Create the code/file content for this task:
{state['goal']}

Output ONLY the file content, no explanations. Include a file path comment at the top if relevant."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        code = response.content

        # Try to extract file path
        filepath = "generated.py"  # default
        if "save as" in state["goal"].lower():
            parts = state["goal"].split("save as")
            if len(parts) > 1:
                filepath = parts[1].strip().split()[0].strip("\"'.")
        elif ".py" in state["goal"]:
            # Extract .py filename
            words = state["goal"].split()
            for w in words:
                if ".py" in w:
                    filepath = w.strip("\"'.,")
                    break

        try:
            result = await write_file(filepath, code)
            await self.log(f"Wrote {filepath} ({result['bytes_written']} bytes)")
            files_written = [filepath]
        except Exception as e:
            await self.log(f"Error writing file: {e}")
            files_written = []

        await self.update_task_progress(state["task_id"], "running", 70)
        return {**state, "files_written": files_written, "progress": 70}

    async def _execute_node(self, state: CodeState) -> CodeState:
        """Execute code/commands."""
        await self.log("Executing code...")

        shell_output = ""
        if state.get("files_written"):
            # Try to run the file
            for f in state["files_written"]:
                if f.endswith(".py"):
                    cmd = f"python {f}"
                    try:
                        result = await execute_shell(cmd)
                        shell_output += f"$ {cmd}\n{result['stdout']}"
                        if result['stderr']:
                            shell_output += f"STDERR: {result['stderr']}"
                        await self.log(f"Executed {f}: exit {result['returncode']}")
                    except Exception as e:
                        shell_output += f"Error executing {f}: {e}"

        await self.update_task_progress(state["task_id"], "running", 90)
        return {**state, "shell_output": shell_output, "progress": 90}

    async def _finalize_node(self, state: CodeState) -> CodeState:
        """Finalize and summarize."""
        await self.set_status("thinking", state["task_id"])
        await self.log("Finalizing code task...")

        # Summarize what was done
        result_parts = []
        if state.get("files_written"):
            result_parts.append(f"Created/modified: {', '.join(state['files_written'])}")
        if state.get("shell_output"):
            result_parts.append(f"Execution output:\n{state['shell_output'][:500]}")

        code_result = "\n\n".join(result_parts) if result_parts else "Task completed"

        return {**state, "code_result": code_result, "status": "complete", "progress": 100}

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Execute code workflow."""
        initial_state: CodeState = {
            "task_id": task_id,
            "goal": goal,
            "files_read": [],
            "files_written": [],
            "shell_output": "",
            "code_result": "",
            "status": "running",
            "progress": 5,
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            await self.update_task_progress(
                task_id,
                status="done",
                progress=100,
                result=final_state["code_result"],
            )

            await self.set_status("idle", None)
            return final_state["code_result"]

        except Exception as e:
            await self.log(f"Error: {str(e)}")
            await self.update_task_progress(task_id, status="failed", progress=0)
            await self.set_status("error", None)
            raise

    def get_agent_info(self):
        """Get agent info with correct tools."""
        return {
            **super().get_agent_info(),
            "toolsUsed": ["fs_read", "fs_write", "shell"],
        }
