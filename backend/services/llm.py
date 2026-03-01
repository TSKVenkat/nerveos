"""LLM service — Ollama (local) with optional OpenAI fallback."""

import httpx
from typing import Optional
from loguru import logger
from config import settings

try:
    import ollama as ollama_lib
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class LLMService:
    """Unified LLM interface: tries Ollama first, falls back to OpenAI-compatible."""

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Generate text from LLM."""
        # Try Ollama first
        result = await self._ollama_generate(prompt, system, temperature)
        if result:
            return result

        # Fallback to OpenAI
        if self.openai_key:
            result = await self._openai_generate(prompt, system, temperature, max_tokens)
            if result:
                return result

        return "[LLM unavailable — configure Ollama or OpenAI]"

    async def _ollama_generate(self, prompt: str, system: str, temperature: float) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                }
                if system:
                    payload["system"] = system

                resp = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "")
        except httpx.ConnectError:
            logger.debug("Ollama not reachable")
        except Exception as e:
            logger.error("Ollama error: {}", e)
        return None

    async def _openai_generate(self, prompt: str, system: str, temperature: float, max_tokens: int) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    json={
                        "model": self.openai_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("OpenAI error: {}", e)
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
