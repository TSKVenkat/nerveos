"""Google Trends integration via pytrends (open-source)."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from loguru import logger

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

_executor = ThreadPoolExecutor(max_workers=2)


class TrendsService:
    """Fetch Google Trends data for keywords and competitors."""

    def __init__(self):
        if PYTRENDS_AVAILABLE:
            self.pytrends = TrendReq(hl="en-US", tz=330)
        else:
            self.pytrends = None
            logger.warning("pytrends not installed – trends features disabled")

    def _interest_over_time(self, keywords: list[str], timeframe: str = "today 3-m"):
        """Synchronous call – will be run in executor."""
        if not self.pytrends:
            return {}
        self.pytrends.build_payload(keywords[:5], cat=0, timeframe=timeframe)
        df = self.pytrends.interest_over_time()
        if df.empty:
            return {}
        df = df.drop(columns=["isPartial"], errors="ignore")
        return {
            "dates": [d.isoformat() for d in df.index],
            "series": {col: df[col].tolist() for col in df.columns},
        }

    async def get_interest_over_time(self, keywords: list[str], timeframe: str = "today 3-m") -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._interest_over_time, keywords, timeframe)

    def _related_queries(self, keyword: str):
        if not self.pytrends:
            return {}
        self.pytrends.build_payload([keyword], cat=0, timeframe="today 3-m")
        related = self.pytrends.related_queries()
        result = {}
        for k, v in related.items():
            result[k] = {}
            if v.get("top") is not None and not v["top"].empty:
                result[k]["top"] = v["top"].head(10).to_dict(orient="records")
            if v.get("rising") is not None and not v["rising"].empty:
                result[k]["rising"] = v["rising"].head(10).to_dict(orient="records")
        return result

    async def get_related_queries(self, keyword: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._related_queries, keyword)

    def _trending_searches(self, country: str = "india"):
        if not self.pytrends:
            return []
        df = self.pytrends.trending_searches(pn=country)
        return df[0].tolist()[:20]

    async def get_trending_searches(self, country: str = "india") -> list[str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._trending_searches, country)


trends_service = TrendsService()
