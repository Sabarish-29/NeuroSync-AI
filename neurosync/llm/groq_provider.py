"""
NeuroSync AI — Groq Cloud API provider implementation.

FREE tier: 30 req/min, unlimited usage.
"""

from __future__ import annotations

import time
from typing import List

from groq import Groq
from loguru import logger

from neurosync.llm.base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class GroqProvider(BaseLLMProvider):
    """
    Groq provider using llama-3.3-70b-versatile.

    Fully compatible with OpenAI interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        super().__init__(api_key, model)
        self.client = Groq(api_key=api_key)
        self.provider_name = "groq"

        # Rate limiting (30 requests/minute)
        self.requests_per_minute = 30
        self.request_timestamps: list[float] = []

    def _check_rate_limit(self) -> None:
        """Enforce 30 requests/minute limit."""
        now = time.time()

        # Remove timestamps older than 60 seconds
        self.request_timestamps = [
            ts for ts in self.request_timestamps if now - ts < 60
        ]

        # Wait if at limit
        if len(self.request_timestamps) >= self.requests_per_minute:
            oldest = self.request_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                logger.warning(
                    "Groq rate limit reached. Waiting {:.1f}s...", wait_time
                )
                time.sleep(wait_time)
                self.request_timestamps = []

        self.request_timestamps.append(now)

    def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion using Groq API."""
        try:
            self._check_rate_limit()

            groq_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            finish_reason = response.choices[0].finish_reason

            logger.info(
                "Groq ({}): {} tokens, finish={}",
                self.model,
                tokens,
                finish_reason,
            )

            return LLMResponse(
                content=content,
                tokens_used=tokens,
                model=self.model,
                provider="groq",
                finish_reason=finish_reason,
            )

        except Exception as e:
            logger.error("Groq API error: {}", e)
            raise

    def is_available(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            test_messages = [LLMMessage(role="user", content="test")]
            self.chat_completion(test_messages, max_tokens=5)
            return True
        except Exception as e:
            logger.warning("Groq unavailable: {}", e)
            return False
