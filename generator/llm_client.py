import json
import logging
import time
from typing import Any, ClassVar

from config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    PROVIDER_CONFIGS: ClassVar[dict[str, dict[str, Any]]] = {
        "groq": {
            "base_url_field": "groq_base_url",
            "api_key_field": "groq_api_key",
            "supports_json_mode": False,
        },
        "openai": {
            "base_url": None,
            "api_key_field": "openai_api_key",
            "supports_json_mode": True,
        },
        "openrouter": {
            "base_url_field": "openrouter_base_url",
            "api_key_field": "openrouter_api_key",
            "supports_json_mode": True,
        },
        "anthropic": {
            "base_url": None,
            "api_key_field": "anthropic_api_key",
            "supports_json_mode": False,
        },
        "huggingface": {
            "base_url_field": "huggingface_base_url",
            "api_key_field": "huggingface_api_key",
            "supports_json_mode": False,
        },
    }

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_calls: int = 0
    usage_log: list[dict] = []

    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self._client = None

    @property
    def config(self) -> dict[str, Any]:
        return self.PROVIDER_CONFIGS.get(self.provider, self.PROVIDER_CONFIGS["groq"])

    @property
    def client(self):
        if self._client is None:
            import openai
            cfg = self.config
            api_key = getattr(settings, cfg["api_key_field"], "")
            kwargs = {"api_key": api_key, "timeout": settings.llm_request_timeout_seconds}
            base_url = self._base_url(cfg)
            if base_url:
                kwargs["base_url"] = base_url
            self._client = openai.OpenAI(**kwargs)
        return self._client

    def _base_url(self, cfg: dict) -> str | None:
        if cfg.get("base_url_field"):
            return getattr(settings, cfg["base_url_field"], "")
        return cfg.get("base_url")

    def generate(self, system_prompt: str, user_prompt: str,
                 temperature: float | None = None, max_tokens: int | None = None,
                 json_mode: bool = True) -> str:
        temp = temperature or settings.llm_temperature
        tokens = max_tokens or settings.llm_max_tokens
        cfg = self.config
        supports_json = cfg.get("supports_json_mode", False)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict[str, Any] = {
            "model": self.model, "messages": messages,
            "temperature": temp, "max_tokens": tokens,
        }
        if json_mode and supports_json:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(1, settings.llm_max_retries + 2):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                if json_mode and not supports_json:
                    content = self._ensure_json(content)
                self._log_usage(response, attempt)
                return content
            except Exception as exc:
                if attempt >= settings.llm_max_retries + 1:
                    raise
                delay = settings.llm_retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(f"LLM attempt {attempt} failed: {exc}, retrying in {delay}s")
                time.sleep(delay)

        raise RuntimeError("LLM retry loop exited unexpectedly")

    def _log_usage(self, response, attempt: int):
        try:
            usage = response.usage
            if usage:
                p = usage.prompt_tokens or 0
                c = usage.completion_tokens or 0
                self.total_prompt_tokens += p
                self.total_completion_tokens += c
                self.total_calls += 1
                self.usage_log.append({
                    "model": self.model,
                    "provider": self.provider,
                    "attempt": attempt,
                    "prompt_tokens": p,
                    "completion_tokens": c,
                })
        except Exception:
            pass

    def _ensure_json(self, text: str) -> str:
        import re
        text = text.strip()
        # Try array first (batch responses), then a single object.
        for pattern in (r"\[.*\]", r"\{.*\}"):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(0)
        return text
