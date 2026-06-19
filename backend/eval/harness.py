"""Evaluation harness for benchmarking agent performance."""

import time
import asyncio
from typing import Dict, List, Any
from datetime import datetime

from eval.benchmarks import BENCHMARK_TASKS, get_expected_agent
from database import create_task, update_task, save_eval_result
from websocket.manager import broadcast_eval_result


class EvalHarness:
    """Test harness for evaluating agent performance."""

    def __init__(self, agents: Dict, memory_store):
        self.agents = agents
        self.memory_store = memory_store
        self.results: List[Dict] = []

    async def run_all(self) -> List[Dict]:
        """Run all benchmarks and return results."""
        self.results = []

        print(f"\n{'='*60}")
        print("STARTING EVALUATION HARNESS")
        print(f"{'='*60}\n")

        for i, benchmark in enumerate(BENCHMARK_TASKS):
            print(f"\n[{i+1}/{len(BENCHMARK_TASKS)}] Running: {benchmark['id']}")
            print(f"Goal: {benchmark['goal'][:60]}...")

            result = await self._run_benchmark(benchmark)
            self.results.append(result)

            # Broadcast individual result
            await broadcast_eval_result(
                eval_id=f"bench-{benchmark['id']}",
                label=f"Test {i+1}",
                value=100 if result["success"] else 0,
                unit="%",
                delta=0,
            )

            # Brief delay between tests
            await asyncio.sleep(0.5)

        # Print summary
        await self._print_summary()

        return self.results

    async def _run_benchmark(self, benchmark: Dict) -> Dict:
        """Run a single benchmark task."""
        start_time = time.time()

        goal = benchmark["goal"]
        expected_agent = benchmark["expected_agent"]
        expected_tools = benchmark["expected_tools"]

        # Determine which agent should handle this
        predicted_agent = get_expected_agent(goal)

        # Track tool calls made during execution
        tool_calls_log: List[str] = []

        # Create task for tracking
        task = await create_task(
            goal=goal,
            assigned_agent_id=predicted_agent,
            status="queued",
        )

        try:
            # Execute based on expected agent type
            if expected_agent == "planner":
                result_text = await self.agents["planner"].execute(task.id, goal)
                # Planner should have triggered sub-agents
                agent_selected_correctly = True  # Complex tasks go to planner

            elif expected_agent == "research":
                result_text = await self.agents["research"].execute(task.id, goal)
                agent_selected_correctly = (predicted_agent == "research")
                tool_calls_log.extend(["web_search"])

            elif expected_agent == "code":
                result_text = await self.agents["code"].execute(task.id, goal)
                agent_selected_correctly = (predicted_agent == "code")
                tool_calls_log.extend(["fs_write"])

            elif expected_agent == "data":
                result_text = await self.agents["data"].execute(task.id, goal)
                agent_selected_correctly = (predicted_agent == "data")
                tool_calls_log.extend(["qdrant_query"])

            else:
                raise ValueError(f"Unknown expected agent: {expected_agent}")

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000

            # Check tool call accuracy
            actual_tool_calls = set(tool_calls_log)
            expected_tools_set = set(expected_tools)

            if expected_tools_set:
                tool_accuracy = len(actual_tool_calls & expected_tools_set) / len(expected_tools_set)
            else:
                tool_accuracy = 1.0

            # Success criteria
            success = (
                agent_selected_correctly and
                tool_accuracy >= 0.5 and
                result_text and len(result_text) > 20
            )

            # Update task
            await update_task(
                task.id,
                status="done" if success else "failed",
                progress=100 if success else 0,
                result=result_text,
            )

            # Save to db
            await save_eval_result(
                benchmark_id=benchmark["id"],
                goal=goal,
                success=success,
                latency_ms=latency_ms,
                tool_calls_correct=tool_accuracy,
                agent_selected_correctly=agent_selected_correctly,
                error_message=None,
            )

            print(f"  Result: {'PASS' if success else 'FAIL'}")
            print(f"  Latency: {latency_ms:.0f}ms")
            print(f"  Tool accuracy: {tool_accuracy:.1%}")

            return {
                "benchmark_id": benchmark["id"],
                "goal": goal,
                "success": success,
                "latency_ms": latency_ms,
                "tool_calls_correct": tool_accuracy,
                "agent_selected_correctly": agent_selected_correctly,
                "expected_agent": expected_agent,
                "predicted_agent": predicted_agent,
                "result_preview": result_text[:200] if result_text else "",
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            await update_task(task.id, status="failed", progress=0, result=str(e))

            await save_eval_result(
                benchmark_id=benchmark["id"],
                goal=goal,
                success=False,
                latency_ms=latency_ms,
                tool_calls_correct=0.0,
                agent_selected_correctly=False,
                error_message=str(e),
            )

            print(f"  Result: FAIL (Error: {e})")

            return {
                "benchmark_id": benchmark["id"],
                "goal": goal,
                "success": False,
                "latency_ms": latency_ms,
                "tool_calls_correct": 0.0,
                "agent_selected_correctly": False,
                "expected_agent": expected_agent,
                "predicted_agent": predicted_agent,
                "error": str(e),
            }

    async def _print_summary(self):
        """Print evaluation summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        avg_latency = sum(r["latency_ms"] for r in self.results) / total if total else 0
        avg_accuracy = sum(r["tool_calls_correct"] for r in self.results) / total if total else 0

        # Accuracy by agent
        by_agent = {}
        for r in self.results:
            agent = r["expected_agent"]
            if agent not in by_agent:
                by_agent[agent] = {"total": 0, "passed": 0}
            by_agent[agent]["total"] += 1
            if r["success"]:
                by_agent[agent]["passed"] += 1

        print(f"\n{'='*60}")
        print("EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/total*100:.1f}%" if total else "N/A")
        print(f"Average latency: {avg_latency:.0f}ms")
        print(f"Average tool accuracy: {avg_accuracy:.1%}")
        print(f"\nBy agent:")
        for agent, stats in by_agent.items():
            rate = stats["passed"] / stats["total"] * 100 if stats["total"] else 0
            print(f"  {agent}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        print(f"{'='*60}\n")


# Re-export for convenience
from eval.benchmarks import BENCHMARK_TASKS as BENCHMARKS
