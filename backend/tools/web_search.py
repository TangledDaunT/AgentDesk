"""Web search tool implementations using DuckDuckGo or SerpAPI."""

import os
import re
from typing import List, Dict
from urllib.parse import urlencode, urlparse
import httpx


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc


async def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo (free, no API key required).

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of search results with title, snippet, and URL
    """
    serpapi_key = os.getenv("SERPAPI_KEY")

    if serpapi_key:
        # Use SerpAPI if key is available
        return await _search_serpapi(query, max_results, serpapi_key)
    else:
        # Use DuckDuckGo (free) as fallback
        return await _search_duckduckgo(query, max_results)


async def _search_serpapi(query: str, max_results: int, api_key: str) -> List[Dict[str, str]]:
    """Search using SerpAPI (Google)."""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "num": max_results,
        "engine": "google",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("organic_results", [])[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
            "source": _extract_domain(item.get("link", "")),
        })

    return results


async def _search_duckduckgo(query: str, max_results: int) -> List[Dict[str, str]]:
    """Search using DuckDuckGo HTML interface (no API key required)."""
    # DuckDuckGo's API requires specific handling
    url = "https://html.duckduckgo.com/html/"
    data = {
        "q": query,
        "kl": "us-en",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers, timeout=30.0)
        response.raise_for_status()
        html = response.text

    results = []

    # Parse DuckDuckGo results
    result_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
    snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>'

    titles = re.findall(result_pattern, html)
    snippets = re.findall(snippet_pattern, html)

    for i, (href, title) in enumerate(titles[:max_results]):
        # Clean up title HTML entities
        title_clean = re.sub(r'<[^>]+>', '', title)
        title_clean = title_clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

        snippet_clean = ""
        if i < len(snippets):
            snippet_clean = re.sub(r'<[^>]+>', '', snippets[i])
            snippet_clean = snippet_clean.replace("&amp;", "&")

        # DuckDuckGo uses redirect URLs - extract actual URL
        if href.startswith("//duckduckgo.com/l/"):
            # Extract uddg parameter
            match = re.search(r'uddg=([^&]+)', href)
            if match:
                import urllib.parse
                actual_url = urllib.parse.unquote(match.group(1))
            else:
                continue
        else:
            actual_url = href

        results.append({
            "title": title_clean,
            "snippet": snippet_clean,
            "url": actual_url,
            "source": _extract_domain(actual_url),
        })

    return results


async def web_fetch(url: str) -> str:
    """
    Fetch and extract text content from a URL.

    Args:
        url: URL to fetch

    Returns:
        Extracted text content (truncated if too long)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
            response.raise_for_status()

            # Basic HTML to text extraction
            text = response.text

            # Remove script/style tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

            # Convert common tags to newlines
            text = re.sub(r'</(p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

            # Remove remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            # Decode HTML entities
            text = text.replace("&amp;", "&")
            text = text.replace("&lt;", "<")
            text = text.replace("&gt;", ">")
            text = text.replace("&quot;", '"')
            text = text.replace("&#39;", "'")

            # Clean up whitespace
            text = re.sub(r'\n+', '\n', text)
            text = re.sub(r' +', ' ', text)

            # Limit to 8000 chars to avoid context overflow
            if len(text) > 8000:
                text = text[:8000] + "\n\n[Content truncated...]"

            return text.strip()

        except Exception as e:
            return f"Error fetching {url}: {str(e)}"
