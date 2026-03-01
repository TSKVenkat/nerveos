"""SearXNG private search integration."""

import httpx
from typing import Optional
from loguru import logger
from config import settings


class SearXNGService:
    """Privacy-friendly web search via a local SearXNG instance."""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or settings.SEARXNG_URL).rstrip("/")

    async def search(
        self,
        query: str,
        categories: str = "general",
        language: str = "en",
        time_range: str = "",
        max_results: int = 10,
    ) -> list[dict]:
        """Run a search query against SearXNG."""
        params = {
            "q": query,
            "format": "json",
            "categories": categories,
            "language": language,
            "pageno": 1,
        }
        if time_range:
            params["time_range"] = time_range  # day, week, month, year

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.base_url}/search", params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])[:max_results]
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                        "engine": r.get("engine", ""),
                        "published_date": r.get("publishedDate", ""),
                    }
                    for r in results
                ]
        except httpx.ConnectError:
            logger.warning("SearXNG not reachable at {}", self.base_url)
            return []
        except Exception as e:
            logger.error("SearXNG search error: {}", e)
            return []

    async def search_news(self, query: str, max_results: int = 10) -> list[dict]:
        return await self.search(query, categories="news", time_range="week", max_results=max_results)

    async def search_it(self, query: str, max_results: int = 10) -> list[dict]:
        return await self.search(query, categories="it", max_results=max_results)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/healthz")
                return resp.status_code == 200
        except Exception:
            return False


searxng_service = SearXNGService()
