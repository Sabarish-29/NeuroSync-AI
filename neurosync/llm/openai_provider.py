"""
NeuroSync AI — OpenAI API provider implementation.

Wrapper around existing OpenAI client.
"""

from __future__ import annotations

from typing import List

from loguru import logger
from openai import OpenAI

from neurosync.llm.base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider wrapper.

    Maintains compatibility with existing code.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
    ) -> None:
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        self.provider_name = "openai"

    def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion using OpenAI API."""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            finish_reason = response.choices[0].finish_reason

            logger.info(
                "OpenAI ({}): {} tokens, finish={}",
                self.model,
                tokens,
                finish_reason,
            )

            return LLMResponse(
                content=content,
                tokens_used=tokens,
                model=self.model,
                provider="openai",
                finish_reason=finish_reason,
            )

        except Exception as e:
            logger.error("OpenAI API error: {}", e)
            raise

    def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            test_messages = [LLMMessage(role="user", content="test")]
            self.chat_completion(test_messages, max_tokens=5)
            return True
        except Exception as e:
            logger.warning("OpenAI unavailable: {}", e)
            return False
