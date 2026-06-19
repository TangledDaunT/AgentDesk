#!/usr/bin/env python3
"""Standalone evaluation script for AgentDesk."""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import init_db
from agents.planner import PlannerAgent
from agents.research import ResearchAgent
from agents.code import CodeAgent
from agents.data import DataAgent
from memory.qdrant_store import QdrantMemoryStore
from eval.harness import EvalHarness


async def main():
    """Run evaluation harness."""
    print("=" * 70)
    print("AGENTDESK EVALUATION HARNESS")
    print("=" * 70)

    # Initialize
    print("\n[1/4] Initializing database...")
    await init_db()

    print("\n[2/4] Loading agents...")
    agents = {
        "planner": PlannerAgent(),
        "research": ResearchAgent(),
        "code": CodeAgent(),
        "data": DataAgent(),
    }

    print("\n[3/4] Connecting to memory store...")
    memory_store = QdrantMemoryStore()

    # Ensure sample data exists
    try:
        results = await memory_store.search("test", limit=1)
        if not results:
            print("Seeding sample data...")
            memory_store.seed_sample_data()
    except Exception as e:
        print(f"Note: {e}")
        memory_store.seed_sample_data()

    print("\n[4/4] Running evaluation...")
    harness = EvalHarness(agents, memory_store)
    results = await harness.run_all()

    # Save detailed results
    output_file = Path("eval_results.json")
    summary = {
        "run_at": datetime.utcnow().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results) if results else 0,
        "avg_tool_accuracy": sum(r["tool_calls_correct"] for r in results) / len(results) if results else 0,
        "detailed_results": results,
    }

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {output_file.absolute()}")
    print(f"\nSummary:")
    print(f"  Success rate: {summary['passed']}/{summary['total']} ({summary['passed']/summary['total']*100:.1f}%)")
    print(f"  Avg latency: {summary['avg_latency_ms']:.0f}ms")
    print(f"  Avg tool accuracy: {summary['avg_tool_accuracy']:.1%}")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
