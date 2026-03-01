"""Financial data service via yfinance (open-source)."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from loguru import logger

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

_executor = ThreadPoolExecutor(max_workers=2)


class FinanceService:
    """Stock prices, company info, and financial data."""

    def _get_stock_info(self, ticker: str) -> dict:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed"}
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "ticker": ticker,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "previous_close": info.get("previousClose", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "revenue": info.get("totalRevenue", 0),
                "profit_margin": info.get("profitMargins", 0),
                "employees": info.get("fullTimeEmployees", 0),
                "website": info.get("website", ""),
                "summary": info.get("longBusinessSummary", "")[:500],
            }
        except Exception as e:
            logger.error("yfinance error for {}: {}", ticker, e)
            return {"ticker": ticker, "error": str(e)}

    async def get_stock_info(self, ticker: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_stock_info, ticker)

    def _get_price_history(self, ticker: str, period: str = "3mo") -> dict:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed"}
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty:
                return {"ticker": ticker, "data": []}
            return {
                "ticker": ticker,
                "dates": [d.isoformat() for d in df.index],
                "close": df["Close"].tolist(),
                "volume": df["Volume"].tolist(),
                "high": df["High"].tolist(),
                "low": df["Low"].tolist(),
            }
        except Exception as e:
            logger.error("yfinance history error: {}", e)
            return {"ticker": ticker, "error": str(e)}

    async def get_price_history(self, ticker: str, period: str = "3mo") -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_price_history, ticker, period)

    def _detect_anomalies(self, ticker: str) -> dict:
        """Simple anomaly detection: large price/volume swings."""
        if not YFINANCE_AVAILABLE:
            return {}
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            if len(df) < 5:
                return {"anomalies": []}
            
            alerts = []
            # Check last day's change
            last_close = df["Close"].iloc[-1]
            prev_close = df["Close"].iloc[-2]
            pct_change = ((last_close - prev_close) / prev_close) * 100

            if abs(pct_change) > 5:
                direction = "surged" if pct_change > 0 else "dropped"
                alerts.append({
                    "type": "price_swing",
                    "message": f"{ticker} {direction} {abs(pct_change):.1f}% in last session",
                    "severity": "critical" if abs(pct_change) > 10 else "warning",
                    "value": round(pct_change, 2),
                })

            # Volume spike
            avg_volume = df["Volume"].iloc[:-1].mean()
            last_volume = df["Volume"].iloc[-1]
            if avg_volume > 0 and last_volume > avg_volume * 2:
                alerts.append({
                    "type": "volume_spike",
                    "message": f"{ticker} volume {last_volume/avg_volume:.1f}x above average",
                    "severity": "warning",
                    "value": round(last_volume / avg_volume, 2),
                })

            return {"ticker": ticker, "anomalies": alerts}
        except Exception as e:
            return {"ticker": ticker, "error": str(e)}

    async def detect_anomalies(self, ticker: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._detect_anomalies, ticker)

    async def get_multiple_stocks(self, tickers: list[str]) -> list[dict]:
        tasks = [self.get_stock_info(t) for t in tickers]
        return await asyncio.gather(*tasks)


finance_service = FinanceService()
