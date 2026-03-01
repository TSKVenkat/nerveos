"""RSS / News feed aggregation service."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import feedparser
import httpx
from loguru import logger

_executor = ThreadPoolExecutor(max_workers=3)

# Curated open RSS sources
DEFAULT_FEEDS = [
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en",
    "https://www.reddit.com/search.rss?q={query}&sort=new&t=week",
]

BUSINESS_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch/",
    "https://www.theverge.com/rss/index.xml",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://hnrss.org/newest?q={query}",
]


class NewsService:
    """Aggregate news from RSS feeds."""

    def _parse_feed(self, url: str) -> list[dict]:
        try:
            feed = feedparser.parse(url)
            items = []
            for entry in feed.entries[:10]:
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).isoformat()
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],
                    "published": published,
                    "source": feed.feed.get("title", url),
                })
            return items
        except Exception as e:
            logger.error("Feed parse error for {}: {}", url, e)
            return []

    async def fetch_news_for_query(self, query: str, max_results: int = 20) -> list[dict]:
        """Search multiple RSS feeds for a query."""
        loop = asyncio.get_event_loop()
        all_feeds = DEFAULT_FEEDS + BUSINESS_FEEDS
        urls = [f.format(query=query) for f in all_feeds]

        tasks = [loop.run_in_executor(_executor, self._parse_feed, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items = []
        for r in results:
            if isinstance(r, list):
                items.extend(r)

        # Deduplicate by title
        seen = set()
        unique = []
        for item in items:
            key = item["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        # Sort by published date descending
        unique.sort(key=lambda x: x.get("published", ""), reverse=True)
        return unique[:max_results]

    async def fetch_competitor_news(self, competitor_name: str, keywords: list[str] = None) -> list[dict]:
        """Get news specifically about a competitor."""
        query = competitor_name
        if keywords:
            query += " " + " OR ".join(keywords[:3])
        return await self.fetch_news_for_query(query)


news_service = NewsService()
