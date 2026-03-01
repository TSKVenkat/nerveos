"""LLM service — Grok via OpenRouter."""

import httpx
from typing import Optional
from loguru import logger
from config import settings


class LLMService:
    """LLM interface using Grok (x-ai) through OpenRouter."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Generate text from Grok via OpenRouter."""
        if not self.api_key:
            return "[LLM unavailable — set OPENROUTER_API_KEY in .env]"

        result = await self._openrouter_generate(prompt, system, temperature, max_tokens)
        if result:
            return result

        return "[LLM request failed — check OpenRouter key and quota]"

    async def _openrouter_generate(self, prompt: str, system: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call OpenRouter chat completions (OpenAI-compatible)."""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://nerveos.app",
                        "X-Title": "NerveOS",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error("OpenRouter {}: {}", resp.status_code, resp.text[:300])
        except Exception as e:
            logger.error("OpenRouter/Grok error: {}", e)
        return None

    async def classify(self, text: str, categories: list[str]) -> str:
        """Classify text into one of the given categories."""
        cats = ", ".join(categories)
        prompt = f"""Classify the following text into exactly ONE of these categories: {cats}

Text: {text[:2000]}

Reply with ONLY the category name, nothing else."""
        result = await self.generate(prompt, system="You are a precise text classifier.")
        # Clean up response
        result = result.strip().lower()
        for cat in categories:
            if cat.lower() in result:
                return cat
        return categories[-1]  # default to last

    async def summarize(self, text: str, max_length: int = 200) -> str:
        prompt = f"""Summarize the following text in {max_length} characters or less:

{text[:3000]}"""
        return await self.generate(prompt, system="You are a concise summarizer.")

    async def draft_email_reply(self, original_subject: str, original_body: str,
                                 context: str = "", tone: str = "professional") -> str:
        prompt = f"""Draft a {tone} reply to the following email.

Original Subject: {original_subject}
Original Email: {original_body[:2000]}

{f'Additional context: {context}' if context else ''}

Write ONLY the reply body (no subject line, no greeting headers like "Subject:" or "From:")."""
        return await self.generate(
            prompt,
            system="You are a professional business email assistant. Write clear, concise replies."
        )

    async def analyze_competitor_intel(self, competitor: str, news: list[dict], trends: dict) -> str:
        news_text = "\n".join([f"- {n['title']}: {n.get('summary', '')[:100]}" for n in news[:10]])
        prompt = f"""Analyze the following intelligence about competitor "{competitor}":

Recent News:
{news_text}

Trends Data: {str(trends)[:1000]}

Provide:
1. Key developments (2-3 bullet points)
2. Potential impact on our business
3. Suggested response actions (1-2)

Be concise and actionable."""
        return await self.generate(
            prompt,
            system="You are a competitive intelligence analyst for a B2B company."
        )

    async def natural_language_query(self, question: str, data_context: str) -> str:
        prompt = f"""Answer the following business question using the data provided.

Question: {question}

Data:
{data_context[:3000]}

Give a clear, data-backed answer. If the data is insufficient, say so."""
        return await self.generate(
            prompt,
            system="You are a business analyst assistant. Be precise and reference specific numbers."
        )


llm_service = LLMService()
