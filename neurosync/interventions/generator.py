"""
NeuroSync AI — Main GPT-4 Intervention Content Generator.

Handles cache lookups, rate limiting, cost tracking, retries, and fallbacks.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from neurosync.config.settings import OPENAI_CONFIG, INTERVENTION_COST_LIMITS
from neurosync.interventions.cache.manager import CacheManager
from neurosync.interventions.cost_tracker import CostTracker
from neurosync.interventions.prompts.application import ApplicationPrompts
from neurosync.interventions.prompts.explain import ExplainPrompts
from neurosync.interventions.prompts.misconception import MisconceptionPrompts
from neurosync.interventions.prompts.plateau import PlateauPrompts
from neurosync.interventions.prompts.rescue import RescuePrompts
from neurosync.interventions.prompts.simplify import SimplifyPrompts
from neurosync.interventions.templates.fallbacks import FallbackTemplates


# ── Data model ──────────────────────────────────────────────────────


class GeneratedContent(BaseModel):
    """Content produced by the intervention generator."""

    intervention_type: str
    content: str
    tokens_used: int = 0
    model: str = ""
    from_cache: bool = False
    generated_at: float = Field(default_factory=time.time)


# ── Prompt router ───────────────────────────────────────────────────

_PROMPT_BUILDERS: dict[str, Any] = {
    "simplify": SimplifyPrompts,
    "explain": ExplainPrompts,
    "misconception": MisconceptionPrompts,
    "rescue": RescuePrompts,
    "plateau": PlateauPrompts,
    "application": ApplicationPrompts,
}

_SYSTEM_BASE = (
    "You are NeuroSync, an AI tutor for high school students. "
    "Your explanations are clear, encouraging, and grade-appropriate. "
    "You never talk down to students or use baby language. "
    "You make complex topics accessible without oversimplifying them."
)

_SYSTEM_SUFFIXES: dict[str, str] = {
    "simplify": " When simplifying, maintain accuracy while reducing complexity.",
    "explain": " When explaining, assume zero prior knowledge and use concrete examples.",
    "misconception": " When addressing misconceptions, be non-judgmental and empathetic.",
    "rescue": " When rescuing from frustration, validate the difficulty and offer a fresh perspective.",
    "plateau": " When using a new method, make the analogy vivid and relatable.",
    "application": " When creating questions, make them require genuine understanding, not just recall.",
}


# ── Generator ───────────────────────────────────────────────────────


class InterventionGenerator:
    """
    Generates intervention content using GPT-4.

    Handles retries, fallbacks, caching, cost tracking, and rate limiting.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        cache_manager: CacheManager | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        import os

        resolved_key = api_key or os.getenv(str(OPENAI_CONFIG["API_KEY_ENV_VAR"]), "")
        self._model = model or str(OPENAI_CONFIG["MODEL_PRODUCTION"])
        self._max_tokens = int(OPENAI_CONFIG["MAX_TOKENS_PER_REQUEST"])
        self._temperature = float(OPENAI_CONFIG["TEMPERATURE"])
        self._timeout = float(OPENAI_CONFIG["TIMEOUT_SECONDS"])
        self._max_retries = int(OPENAI_CONFIG["MAX_RETRIES"])

        # OpenAI client — lazy-initialized so tests can mock it
        self._api_key = resolved_key
        self._client: Any = None

        self.cache = cache_manager or CacheManager()
        self.cost_tracker = cost_tracker or CostTracker()
        self.fallback_templates = FallbackTemplates()

        # Rate limiting
        self.max_requests_per_minute = int(INTERVENTION_COST_LIMITS["RATE_LIMIT_PER_MINUTE"])
        self.request_count = 0
        self.request_window_start = time.time()

        logger.info("InterventionGenerator initialised (model={})", self._model)

    # ── lazy client ─────────────────────────────────────────────────

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    # ── public API ──────────────────────────────────────────────────

    async def generate(
        self,
        intervention_type: str,
        context: dict[str, Any],
        priority: str = "normal",
    ) -> GeneratedContent:
        """
        Main entry point for content generation.

        Parameters
        ----------
        intervention_type
            One of: simplify, explain, misconception, rescue, plateau, application
        context
            Dictionary with all necessary input data for the prompt builder.
        priority
            ``"critical"`` bypasses rate limits; ``"normal"`` respects them.
        """
        # 1. Cache check
        cache_key = self._generate_cache_key(intervention_type, context)
        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache HIT for {}", intervention_type)
            return cached

        logger.debug("Cache MISS for {}", intervention_type)

        # 2. Cost limit check
        if not self.cost_tracker.can_afford_request():
            logger.warning("Cost limit exceeded — using fallback template")
            return self._generate_fallback(intervention_type, context)

        # 3. Rate limit check
        if not self._can_make_request():
            if priority != "critical":
                logger.warning("Rate limit reached — using fallback")
                return self._generate_fallback(intervention_type, context)

        # 4. Build prompt
        prompt = self._build_prompt(intervention_type, context)

        # 5. Call GPT-4 with retries
        try:
            response = await self._call_gpt4(prompt, intervention_type)

            self.cost_tracker.record_request(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                model=self._model,
            )

            content = self._parse_response(response, intervention_type)
            await self.cache.set(cache_key, content)
            return content

        except Exception as exc:
            logger.error("GPT-4 generation failed: {}", exc)
            return self._generate_fallback(intervention_type, context)

    # ── internal helpers ────────────────────────────────────────────

    async def _call_gpt4(self, prompt: str, intervention_type: str) -> Any:
        """Call the OpenAI API with exponential-backoff retries."""
        client = self._get_client()

        for attempt in range(self._max_retries):
            try:
                response = await client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(intervention_type)},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    timeout=self._timeout,
                )
                self._record_request()
                return response
            except Exception:
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)

    def _build_prompt(self, intervention_type: str, context: dict[str, Any]) -> str:
        builder = _PROMPT_BUILDERS.get(intervention_type)
        if builder is None:
            raise ValueError(f"Unknown intervention type: {intervention_type}")
        return builder.build(context)

    def _get_system_prompt(self, intervention_type: str) -> str:
        return _SYSTEM_BASE + _SYSTEM_SUFFIXES.get(intervention_type, "")

    def _generate_cache_key(self, intervention_type: str, context: dict[str, Any]) -> str:
        sorted_ctx = json.dumps(context, sort_keys=True, default=str)
        combined = f"{intervention_type}:{sorted_ctx}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _parse_response(self, response: Any, intervention_type: str) -> GeneratedContent:
        content_text = response.choices[0].message.content.strip()
        return GeneratedContent(
            intervention_type=intervention_type,
            content=content_text,
            tokens_used=response.usage.total_tokens,
            model=self._model,
            from_cache=False,
        )

    def _generate_fallback(self, intervention_type: str, context: dict[str, Any]) -> GeneratedContent:
        content = self.fallback_templates.generate(intervention_type, context)
        # fallback may return str or list – normalise to str
        if isinstance(content, list):
            content = json.dumps(content)
        return GeneratedContent(
            intervention_type=intervention_type,
            content=content,
            tokens_used=0,
            model="fallback_template",
            from_cache=False,
        )

    # ── rate limiting ───────────────────────────────────────────────

    def _can_make_request(self) -> bool:
        now = time.time()
        if now - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = now
        return self.request_count < self.max_requests_per_minute

    def _record_request(self) -> None:
        self.request_count += 1
