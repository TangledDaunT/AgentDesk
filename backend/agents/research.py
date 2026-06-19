"""Research agent with web search capabilities."""

import json
from typing import Dict, Any

from langchain_core.tools import tool, Tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from agents.base import BaseAgent
from tools.web_search import web_search, web_fetch


class ResearchState(TypedDict):
    """State for research agent."""
    task_id: str
    goal: str
    search_queries: list
    results: list
    synthesis: str
    status: str
    progress: float


class ResearchAgent(BaseAgent):
    """Agent that performs web research."""

    def __init__(self):
        super().__init__(
            agent_id="research",
            name="Research agent",
            role="research",
            description="Web search and source synthesis via MCP",
        )

        # Create LangChain tools
        self.search_tool = Tool(
            name="web_search",
            func=lambda q: web_search(q),  # Will be async in execute
            description="Search the web for information. Input should be a search query.",
        )

        self.fetch_tool = Tool(
            name="web_fetch",
            func=lambda u: web_fetch(u),
            description="Fetch and extract text from a URL. Input should be a URL.",
        )

        self.tools = [self.search_tool, self.fetch_tool]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools([
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "web_fetch",
                "description": "Fetch text content from a URL",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                    },
                    "required": ["url"],
                },
            },
        ])

        # Build LangGraph workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow."""
        builder = StateGraph(ResearchState)

        builder.add_node("plan", self._plan_node)
        builder.add_node("search", self._search_node)
        builder.add_node("fetch", self._fetch_node)
        builder.add_node("synthesize", self._synthesize_node)

        builder.set_entry_point("plan")
        builder.add_edge("plan", "search")
        builder.add_edge("search", "fetch")
        builder.add_edge("fetch", "synthesize")
        builder.add_edge("synthesize", END)

        return builder.compile()

    async def _plan_node(self, state: ResearchState) -> ResearchState:
        """Plan search queries."""
        await self.set_status("thinking", state["task_id"])
        await self.update_task_progress(state["task_id"], "running", 20)
        await self.log("Planning search strategy...")

        prompt = f"""Given this research goal: {state['goal']}

Generate 2-3 specific search queries to gather comprehensive information.
Output as a JSON array of query strings."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        # Extract queries from response
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            queries = json.loads(content.strip())
            if not isinstance(queries, list):
                queries = [content.strip()]
        except Exception:
            # Fallback: split by newlines
            queries = [q.strip("- ") for q in content.strip().split("\n") if q.strip()][:3]

        return {**state, "search_queries": queries, "progress": 30}

    async def _search_node(self, state: ResearchState) -> ResearchState:
        """Execute web searches."""
        await self.set_status("active", state["task_id"])
        await self.log(f"Executing {len(state['search_queries'])} searches...")

        all_results = []
        for i, query in enumerate(state["search_queries"]):
            await self.log(f"Search {i+1}: {query}")
            results = await web_search(query, max_results=3)
            all_results.extend(results)
            await self.update_task_progress(state["task_id"], "running", 30 + (i + 1) * 10)

        return {**state, "results": all_results, "progress": 60}

    async def _fetch_node(self, state: ResearchState) -> ResearchState:
        """Fetch detailed content from top results."""
        await self.log("Fetching content from sources...")

        # Fetch top 3 unique domains
        seen_domains = set()
        to_fetch = []
        for r in state["results"]:
            domain = r.get("source", "")
            if domain and domain not in seen_domains and len(to_fetch) < 3:
                seen_domains.add(domain)
                to_fetch.append(r["url"])

        detailed = []
        for i, url in enumerate(to_fetch):
            await self.log(f"Fetching: {url}")
            content = await web_fetch(url)
            detailed.append({"url": url, "content": content[:2000]})

        return {**state, "results": state["results"] + detailed, "progress": 80}

    async def _synthesize_node(self, state: ResearchState) -> ResearchState:
        """Synthesize findings."""
        await self.set_status("thinking", state["task_id"])
        await self.update_task_progress(state["task_id"], "running", 90)
        await self.log("Synthesizing research findings...")

        # Prepare context
        results_summary = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\n{r.get('snippet', r.get('content', ''))[:500]}"
            for r in state["results"][:5]
        ])

        prompt = f"""Research goal: {state['goal']}

Sources found:
{results_summary}

Provide a concise synthesis (2-3 paragraphs) answering the research goal.
Include key sources used."""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        synthesis = response.content
        await self.log("Research synthesis complete")

        return {**state, "synthesis": synthesis, "status": "complete", "progress": 100}

    async def execute(self, task_id: str, goal: str, context: Dict[str, Any] = None) -> str:
        """Execute research workflow."""
        initial_state: ResearchState = {
            "task_id": task_id,
            "goal": goal,
            "search_queries": [],
            "results": [],
            "synthesis": "",
            "status": "running",
            "progress": 10,
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            # Update task to done
            await self.update_task_progress(
                task_id,
                status="done",
                progress=100,
                result=final_state["synthesis"],
            )

            await self.set_status("idle", None)

            return final_state["synthesis"]

        except Exception as e:
            await self.log(f"Error: {str(e)}")
            await self.update_task_progress(task_id, status="failed", progress=0)
            await self.set_status("error", None)
            raise

    def get_agent_info(self):
        """Get agent info with correct tools."""
        return {
            **super().get_agent_info(),
            "toolsUsed": ["web_search", "web_fetch"],
        }
