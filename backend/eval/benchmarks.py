"""Benchmark definitions for evaluation harness."""

from typing import Dict, List, Tuple

# Define 15-20 benchmark tasks with expected outcomes
BENCHMARK_TASKS = [
    # Research tasks
    {
        "id": "bench-001",
        "goal": "Find recent benchmarks comparing vector DB latency at 5M+ document scale",
        "expected_agent": "research",
        "expected_tools": ["web_search"],
        "difficulty": "medium",
        "category": "research",
    },
    {
        "id": "bench-002",
        "goal": "Search for the latest Claude model version and its context window size",
        "expected_agent": "research",
        "expected_tools": ["web_search"],
        "difficulty": "easy",
        "category": "research",
    },
    {
        "id": "bench-003",
        "goal": "Find information about MCP (Model Context Protocol) tools and their adoption",
        "expected_agent": "research",
        "expected_tools": ["web_search", "web_fetch"],
        "difficulty": "medium",
        "category": "research",
    },
    {
        "id": "bench-004",
        "goal": "Look up Python Redis client best practices for pub/sub",
        "expected_agent": "research",
        "expected_tools": ["web_search"],
        "difficulty": "easy",
        "category": "research",
    },
    {
        "id": "bench-005",
        "goal": "Research current state of multi-agent frameworks in 2025",
        "expected_agent": "research",
        "expected_tools": ["web_search"],
        "difficulty": "hard",
        "category": "research",
    },

    # Code tasks
    {
        "id": "bench-006",
        "goal": "Create a Python function to calculate Fibonacci numbers recursively",
        "expected_agent": "code",
        "expected_tools": ["fs_write"],
        "difficulty": "easy",
        "category": "code",
    },
    {
        "id": "bench-007",
        "goal": "Write a Python script that fetches JSON from an API and saves it to a file",
        "expected_agent": "code",
        "expected_tools": ["fs_write", "shell"],
        "difficulty": "medium",
        "category": "code",
    },
    {
        "id": "bench-008",
        "goal": "Create a simple FastAPI endpoint that returns current timestamp",
        "expected_agent": "code",
        "expected_tools": ["fs_write"],
        "difficulty": "medium",
        "category": "code",
    },
    {
        "id": "bench-009",
        "goal": "Write a shell script to list all Python files in a directory",
        "expected_agent": "code",
        "expected_tools": ["fs_write", "shell"],
        "difficulty": "easy",
        "category": "code",
    },
    {
        "id": "bench-010",
        "goal": "Create a Python class for a simple queue data structure with enqueue and dequeue",
        "expected_agent": "code",
        "expected_tools": ["fs_write"],
        "difficulty": "easy",
        "category": "code",
    },

    # Data tasks
    {
        "id": "bench-011",
        "goal": "Query for similar documents about vector database performance",
        "expected_agent": "data",
        "expected_tools": ["qdrant_query"],
        "difficulty": "medium",
        "category": "data",
    },
    {
        "id": "bench-012",
        "goal": "Retrieve memories about Redis caching results",
        "expected_agent": "data",
        "expected_tools": ["qdrant_query"],
        "difficulty": "easy",
        "category": "data",
    },
    {
        "id": "bench-013",
        "goal": "Find similar cases for query: 'multi-agent orchestration latency'",
        "expected_agent": "data",
        "expected_tools": ["qdrant_query"],
        "difficulty": "medium",
        "category": "data",
    },
    {
        "id": "bench-014",
        "goal": "Search memory for lessons about web search timeouts",
        "expected_agent": "data",
        "expected_tools": ["qdrant_query"],
        "difficulty": "easy",
        "category": "data",
    },
    {
        "id": "bench-015",
        "goal": "Query for outcomes related to code agent tool-call accuracy",
        "expected_agent": "data",
        "expected_tools": ["qdrant_query"],
        "difficulty": "hard",
        "category": "data",
    },

    # Complex tasks (should trigger planner)
    {
        "id": "bench-016",
        "goal": "Research LangGraph memory management, then write a summary document",
        "expected_agent": "planner",
        "expected_tools": ["web_search", "fs_write"],
        "difficulty": "hard",
        "category": "complex",
    },
    {
        "id": "bench-017",
        "goal": "Find Qdrant best practices and query examples, compile them into a report",
        "expected_agent": "planner",
        "expected_tools": ["web_search", "fs_write"],
        "difficulty": "hard",
        "category": "complex",
    },
    {
        "id": "bench-018",
        "goal": "Research Redis pub/sub patterns, then create example code",
        "expected_agent": "planner",
        "expected_tools": ["web_search", "fs_write"],
        "difficulty": "hard",
        "category": "complex",
    },
]


def get_expected_agent(goal: str) -> str:
    """Determine expected agent based on goal content."""
    goal_lower = goal.lower()

    # Check for data/retrieval keywords
    data_keywords = ["query", "retrieve", "search memory", "find similar", "qdrant"]
    if any(kw in goal_lower for kw in data_keywords):
        return "data"

    # Check for code keywords
    code_keywords = ["create", "write", "script", "function", "class", "code", "file"]
    if any(kw in goal_lower for kw in code_keywords):
        return "code"

    # Check for research keywords
    research_keywords = ["find", "search", "look up", "research", "latest"]
    if any(kw in goal_lower for kw in research_keywords):
        return "research"

    # Complex tasks with multiple actions
    if any(kw in goal_lower for kw in ["then", "and", "compile", "report"]):
        return "planner"

    return "research"  # default


# Convenience export
BENCHMARKS = BENCHMARK_TASKS
