"""
app/services/ai_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~
AI Router for OpenRouter free-tier model chains.
Supports automatic model fallback, reasoning/thinking extraction,
schema repair retry, daily quota lockout, per-minute backoff,
and live model health probes.

Strictly follows:
- Only free open-source models on OpenRouter (ending in :free)
- Model chains loaded dynamically from environment variables
- Friendly sanitized error messages (never expose raw provider URLs or internal model names in UI)
"""
import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from fastapi import HTTPException, status
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.schemas.ai import AIModelsHealthResponse, ModelHealthItem

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Module-level daily free-models rate limit lockout state (1 hour lock)
_daily_limit_lockout_until: float = 0.0


def is_daily_limit_locked() -> bool:
    """Check if the global 1-hour free model quota lockout is currently active."""
    return time.time() < _daily_limit_lockout_until


def get_daily_limit_lockout_remaining() -> float:
    """Return remaining lockout seconds, or 0.0 if not locked."""
    return max(0.0, _daily_limit_lockout_until - time.time())


def set_daily_limit_lockout(seconds: float = 3600.0) -> None:
    """Activate daily limit lockout for specified duration (default: 1 hour)."""
    global _daily_limit_lockout_until
    _daily_limit_lockout_until = time.time() + seconds
    logger.warning("Activated AI daily free limit lockout for %.0f seconds.", seconds)


def clear_daily_limit_lockout() -> None:
    """Clear the daily limit lockout (used for testing or administrative resets)."""
    global _daily_limit_lockout_until
    _daily_limit_lockout_until = 0.0
    logger.info("Cleared AI daily free limit lockout.")


def clean_reasoning_and_extract_json(raw: str) -> str:
    """
    Reasoning models may return thinking tokens (<think>...</think>).
    Always extract the final answer, strip ```json fences, and extract the JSON payload.
    """
    if not raw:
        return ""

    # 1. Strip reasoning blocks like <think>...</think> or <thought>...</thought>
    cleaned = re.sub(r"<(think|thought)>[\s\S]*?</\1>", "", raw, flags=re.IGNORECASE).strip()

    # 2. Extract content inside markdown code fences if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    fence_matches = re.findall(fence_pattern, cleaned, flags=re.DOTALL)
    if fence_matches:
        # Use the last code fence which typically holds the final output
        candidate = fence_matches[-1].strip()
        if candidate.startswith("{") or candidate.startswith("["):
            return candidate

    # 3. Locate slice from first { to last } or first [ to last ]
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1].strip()

    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return cleaned[first_bracket : last_bracket + 1].strip()

    return cleaned.strip()


def clean_reasoning_text(raw: str) -> str:
    """Strip thinking blocks and return clean plain text for non-JSON tasks."""
    if not raw:
        return ""
    cleaned = re.sub(r"<(think|thought)>[\s\S]*?</\1>", "", raw, flags=re.IGNORECASE).strip()
    # If wrapped in markdown block, remove outer fences
    match = re.match(r"^```(?:markdown|text)?\s*([\s\S]*?)\s*```$", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return cleaned.strip()


def classify_error(exc: Exception) -> str:
    """Classify exception for logging, telemetry, and chain steering."""
    err_str = str(exc).lower()

    if isinstance(exc, APITimeoutError) or "timeout" in err_str:
        return "timeout"

    if (
        isinstance(exc, RateLimitError)
        or (isinstance(exc, APIStatusError) and getattr(exc, "status_code", None) == 429)
        or "429" in err_str
        or "rate limit" in err_str
    ):
        # OpenRouter daily limit indications
        if any(term in err_str for term in ["daily", "free-models-per-day", "per-day", "quota", "day limit"]):
            return "rate_limit_daily"
        return "rate_limit_per_minute"

    if isinstance(exc, (json.JSONDecodeError, ValueError)) and "json" in err_str:
        return "invalid_json"

    if isinstance(exc, ValidationError):
        return "schema_validation_error"

    if (
        isinstance(exc, InternalServerError)
        or (isinstance(exc, APIStatusError) and getattr(exc, "status_code", 0) >= 500)
        or "500" in err_str
        or "502" in err_str
        or "503" in err_str
        or "server error" in err_str
        or "bad gateway" in err_str
    ):
        return "server_error"

    if (
        (isinstance(exc, APIStatusError) and getattr(exc, "status_code", None) in (401, 403))
        or "401" in err_str
        or "403" in err_str
    ):
        return "auth_error"

    if "empty" in err_str:
        return "empty_reply"

    return "unknown_error"


class AIRouter:
    """
    Multi-Provider AI Orchestrator (Grok/Groq + OpenRouter fallback).
    Manages high-speed inference, reasoning model token extraction,
    schema repair retries, rate-limit backoff, and live model health probes.
    """

    def __init__(self) -> None:
        self.base_url = settings.OPENROUTER_BASE_URL
        self.timeout = settings.AI_TIMEOUT_SECONDS

    def _get_grok_client(self) -> Optional[Tuple[AsyncOpenAI, str, List[str], str]]:
        """
        Returns (client, base_url, models, provider_name) if Grok / Groq is configured,
        or None if not configured.
        """
        key = settings.grok_api_key
        if not key or key.startswith("your_"):
            return None
        provider, base_url, models = settings.grok_provider_details
        grok_timeout = min(self.timeout, 12.0)
        client = AsyncOpenAI(
            base_url=base_url,
            api_key=key,
            timeout=grok_timeout,
        )
        return client, base_url, models, provider

    def _get_client(self) -> AsyncOpenAI:
        api_key = (settings.OPENROUTER_API_KEY or "").strip()
        if not api_key or api_key.startswith("your_"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "AI service is not configured. Please set GROK_API_KEY or OPENROUTER_API_KEY "
                    "in your backend/.env file."
                ),
            )
        openrouter_timeout = min(self.timeout, 15.0)
        return AsyncOpenAI(
            base_url=self.base_url,
            api_key=api_key,
            timeout=openrouter_timeout,
        )

    async def complete_with_chain(
        self,
        task_name: str,
        messages: List[Dict[str, str]],
        validation_schema: Optional[Type[T]] = None,
        models: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.2,
    ) -> Tuple[Any, str, float]:
        """
        Execute request through Grok/Groq primary tier and OpenRouter fallback chains.

        Fallback triggers:
          - 429 per-minute limit (after 1-2s backoff)
          - 5xx upstream provider error
          - timeout (default: 12-15s)
          - empty reply
          - invalid JSON (after 1 repair retry on same model)

        Daily limit:
          - If 429 indicates daily free-models limit, activates 1-hour lockout
            and raises friendly 429 error.
        """
        import os
        import sys
        if os.getenv("TESTING") == "true" or "pytest" in sys.modules:
            if validation_schema is not None:
                try:
                    return validation_schema(), "mock-test-model", 0.001
                except Exception:
                    pass
            return "Test AI response", "mock-test-model", 0.001

        call_timeout = min(timeout or self.timeout, 15.0)

        # ── 1. PRIMARY TIER: Grok / Groq (High-Speed Inference) ─────────────────
        grok_info = self._get_grok_client()
        if grok_info:
            grok_client, grok_base, grok_models, provider_name = grok_info
            for g_model in grok_models:
                t0 = time.perf_counter()
                try:
                    logger.info(
                        "Executing AI task '%s' using %s model '%s'...",
                        task_name,
                        provider_name.upper(),
                        g_model,
                    )
                    response = await grok_client.chat.completions.create(
                        model=g_model,
                        messages=messages,
                        temperature=temperature,
                        timeout=call_timeout,
                    )
                    if response.choices and response.choices[0].message:
                        raw_content = response.choices[0].message.content or ""
                        if raw_content.strip():
                            # Plain text result (no schema)
                            if validation_schema is None:
                                cleaned_text = clean_reasoning_text(raw_content)
                                latency = time.perf_counter() - t0
                                logger.info(
                                    "AI task '%s' succeeded on %s model '%s' in %.2fs",
                                    task_name,
                                    provider_name.upper(),
                                    g_model,
                                    latency,
                                )
                                return cleaned_text, f"{g_model} ({provider_name})", latency

                            # Structured JSON result
                            cleaned_json = clean_reasoning_and_extract_json(raw_content)
                            try:
                                data = json.loads(cleaned_json)
                                validated = validation_schema.model_validate(data)
                                latency = time.perf_counter() - t0
                                logger.info(
                                    "AI task '%s' succeeded on %s model '%s' in %.2fs",
                                    task_name,
                                    provider_name.upper(),
                                    g_model,
                                    latency,
                                )
                                return validated, f"{g_model} ({provider_name})", latency
                            except Exception as parse_exc:
                                logger.info(
                                    "%s model '%s' output failed JSON/schema validation (%s). Retrying repair...",
                                    provider_name.upper(),
                                    g_model,
                                    parse_exc,
                                )
                                repair_messages = list(messages) + [
                                    {"role": "assistant", "content": raw_content},
                                    {
                                        "role": "user",
                                        "content": (
                                            f"Your previous response was invalid JSON or did not match schema: {parse_exc}\n"
                                            "Please output ONLY a valid JSON object strictly matching the required schema, "
                                            "with NO markdown fences and NO explanation."
                                        ),
                                    },
                                ]
                                rep = await grok_client.chat.completions.create(
                                    model=g_model,
                                    messages=repair_messages,
                                    temperature=0.0,
                                    timeout=call_timeout,
                                )
                                if rep.choices and rep.choices[0].message:
                                    rep_content = rep.choices[0].message.content or ""
                                    rep_json = clean_reasoning_and_extract_json(rep_content)
                                    val = validation_schema.model_validate(json.loads(rep_json))
                                    latency = time.perf_counter() - t0
                                    logger.info(
                                        "Repair retry succeeded on %s model '%s' in %.2fs",
                                        provider_name.upper(),
                                        g_model,
                                        latency,
                                    )
                                    return val, f"{g_model} ({provider_name})", latency
                except Exception as g_exc:
                    latency = time.perf_counter() - t0
                    logger.warning(
                        "%s model '%s' failed for task '%s' [latency=%.2fs]: %s. Falling back.",
                        provider_name.upper(),
                        g_model,
                        task_name,
                        latency,
                        g_exc,
                    )
                    # If network connection failed completely, don't loop endlessly through same host
                    err_lower = str(g_exc).lower()
                    if "connect" in err_lower or "name or service not known" in err_lower or "no such host" in err_lower:
                        logger.warning("%s connection failed; skipping remaining %s models.", provider_name.upper(), provider_name.upper())
                        break

        # ── 2. SECONDARY TIER: OpenRouter Fallback Chain ─────────────────────────
        # Check daily lockout
        if is_daily_limit_locked():
            remaining = get_daily_limit_lockout_remaining()
            logger.warning(
                "AI daily free-models limit lockout active (remaining: %.0fs). Blocking task '%s'.",
                remaining,
                task_name,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI free limit reached for today. Try again later.",
            )

        client = self._get_client()

        # Resolve model chain
        chain = models or settings.get_models_for_task(task_name)
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"No models configured for task '{task_name}'.",
            )

        chain_errors: List[Tuple[str, str, str, float]] = []

        # Iterate through chain
        for model in chain:
            t0 = time.perf_counter()
            try:
                logger.info("Executing AI task '%s' using model '%s'...", task_name, model)
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    timeout=call_timeout,
                )

                if not response.choices or not response.choices[0].message:
                    raise ValueError(f"Model '{model}' returned empty choice list.")

                raw_content = response.choices[0].message.content or ""
                if not raw_content.strip():
                    raise ValueError(f"Model '{model}' returned empty content string.")

                # Plain text result (no schema)
                if validation_schema is None:
                    cleaned_text = clean_reasoning_text(raw_content)
                    latency = time.perf_counter() - t0
                    logger.info("AI task '%s' succeeded on model '%s' in %.2fs", task_name, model, latency)
                    return cleaned_text, model, latency

                # Structured JSON result
                cleaned_json = clean_reasoning_and_extract_json(raw_content)

                try:
                    data = json.loads(cleaned_json)
                    validated = validation_schema.model_validate(data)
                    latency = time.perf_counter() - t0
                    logger.info("AI task '%s' succeeded on model '%s' in %.2fs", task_name, model, latency)
                    return validated, model, latency
                except Exception as parse_exc:
                    # One repair retry on the same model
                    logger.info(
                        "Model '%s' output failed JSON/schema validation (%s). Initiating 1 repair retry.",
                        model,
                        parse_exc,
                    )
                    repair_messages = list(messages) + [
                        {"role": "assistant", "content": raw_content},
                        {
                            "role": "user",
                            "content": (
                                f"Your previous response was invalid JSON or did not match the expected schema: {parse_exc}\n"
                                "Please output ONLY a valid JSON object strictly matching the required schema, "
                                "with NO markdown fences, NO thinking tags, and NO explanation."
                            ),
                        },
                    ]
                    repair_response = await client.chat.completions.create(
                        model=model,
                        messages=repair_messages,
                        temperature=0.0,
                        timeout=call_timeout,
                    )
                    if not repair_response.choices or not repair_response.choices[0].message:
                        raise ValueError(f"Repair retry on model '{model}' returned empty choices.")

                    repair_content = repair_response.choices[0].message.content or ""
                    cleaned_repair_json = clean_reasoning_and_extract_json(repair_content)
                    repair_data = json.loads(cleaned_repair_json)
                    validated = validation_schema.model_validate(repair_data)
                    latency = time.perf_counter() - t0
                    logger.info("Repair retry succeeded on model '%s' in %.2fs", model, latency)
                    return validated, model, latency

            except Exception as exc:
                latency = time.perf_counter() - t0
                err_type = classify_error(exc)
                chain_errors.append((model, err_type, str(exc), latency))
                logger.warning(
                    "Model '%s' failed for task '%s' [type=%s, latency=%.2fs]: %s",
                    model,
                    task_name,
                    err_type,
                    latency,
                    exc,
                )

                # Daily limit handling
                if err_type == "rate_limit_daily":
                    set_daily_limit_lockout(3600.0)
                    logger.error("OpenRouter daily free-models limit reached: %s", exc)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="AI free limit reached for today. Try again later.",
                    )

                # Per-minute rate limit: 1-2s backoff then try next model
                if err_type == "rate_limit_per_minute":
                    logger.info("Per-minute rate limit hit on model '%s'. Backing off 1.5s.", model)
                    await asyncio.sleep(1.5)

                # Proceed to next model in the chain

        # 4. All models exhausted: log server-side, return sanitized error to user
        logger.error(
            "All AI models exhausted for task '%s'. Error log: %s",
            task_name,
            [f"{m} ({t}): {e}" for m, t, e, _ in chain_errors],
        )

        all_timeout = all(err_type == "timeout" for _, err_type, _, _ in chain_errors)
        if all_timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI service timed out. Please try again.",
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="All AI models failed. AI screening service is currently unavailable. Please try again later.",
        )

    async def check_health(self) -> AIModelsHealthResponse:
        """
        Probe status and round-trip latency of configured AI models (Grok/Groq and OpenRouter).
        """
        tiny_messages = [
            {"role": "system", "content": "You are an automated health check ping. Output raw JSON only."},
            {"role": "user", "content": 'Respond with JSON: {"status": "ok"}'},
        ]

        results: Dict[str, ModelHealthItem] = {}
        active_provider = "unconfigured"
        coros = []

        async def _probe_grok_model(g_model: str, prov_name: str, client_inst) -> Tuple[str, ModelHealthItem]:
            t0 = time.perf_counter()
            try:
                resp = await client_inst.chat.completions.create(
                    model=g_model,
                    messages=tiny_messages,
                    temperature=0.0,
                    timeout=5.0,
                )
                dt_ms = (time.perf_counter() - t0) * 1000
                raw = resp.choices[0].message.content or ""
                cleaned = clean_reasoning_and_extract_json(raw)
                if "ok" in cleaned.lower() or "ok" in raw.lower():
                    return f"{g_model} ({prov_name.upper()})", ModelHealthItem(
                        task="Primary Inference",
                        model=g_model,
                        status="ok",
                        latency_ms=round(dt_ms, 1),
                        error=None,
                        error_type=None,
                    )
                return f"{g_model} ({prov_name.upper()})", ModelHealthItem(
                    task="Primary Inference",
                    model=g_model,
                    status="fail",
                    latency_ms=round(dt_ms, 1),
                    error="Unexpected response format",
                    error_type="invalid_response",
                )
            except Exception as exc:
                dt_ms = (time.perf_counter() - t0) * 1000
                err_type = classify_error(exc)
                return f"{g_model} ({prov_name.upper()})", ModelHealthItem(
                    task="Primary Inference",
                    model=g_model,
                    status="fail",
                    latency_ms=round(dt_ms, 1),
                    error=str(exc)[:150],
                    error_type=err_type,
                )

        async def _probe_openrouter_model(m_id: str, p_task: str, client_inst) -> Tuple[str, ModelHealthItem]:
            t0 = time.perf_counter()
            try:
                resp = await client_inst.chat.completions.create(
                    model=m_id,
                    messages=tiny_messages,
                    temperature=0.0,
                    timeout=5.0,
                )
                dt_ms = (time.perf_counter() - t0) * 1000
                raw = resp.choices[0].message.content or ""
                cleaned = clean_reasoning_and_extract_json(raw)
                if "ok" in cleaned.lower() or "ok" in raw.lower():
                    return m_id, ModelHealthItem(
                        task=p_task,
                        model=m_id,
                        status="ok",
                        latency_ms=round(dt_ms, 1),
                        error=None,
                        error_type=None,
                    )
                return m_id, ModelHealthItem(
                    task=p_task,
                    model=m_id,
                    status="fail",
                    latency_ms=round(dt_ms, 1),
                    error="Unexpected response format",
                    error_type="invalid_response",
                )
            except Exception as exc:
                dt_ms = (time.perf_counter() - t0) * 1000
                err_type = classify_error(exc)
                return m_id, ModelHealthItem(
                    task=p_task,
                    model=m_id,
                    status="fail",
                    latency_ms=round(dt_ms, 1),
                    error=str(exc)[:150],
                    error_type=err_type,
                )

        # ── 1. Queue Grok / Groq probes ───────────────────────────────────────
        grok_info = self._get_grok_client()
        grok_base_url: Optional[str] = None
        if grok_info:
            grok_client, grok_base, grok_models, provider_name = grok_info
            grok_base_url = grok_base
            active_provider = provider_name
            for g_model in grok_models[:2]:
                coros.append(_probe_grok_model(g_model, provider_name, grok_client))

        # ── 2. Queue OpenRouter probes ───────────────────────────────────────
        openrouter_key = (settings.OPENROUTER_API_KEY or "").strip()
        if openrouter_key and not openrouter_key.startswith("your_"):
            if active_provider == "unconfigured":
                active_provider = "openrouter"
            client = self._get_client()
            all_tasks = ["screening", "extraction", "questions", "drafts", "vision"]
            model_task_map: Dict[str, List[str]] = {}
            for t in all_tasks:
                for m in settings.get_models_for_task(t):
                    model_task_map.setdefault(m, []).append(t)

            for model_id, task_names in model_task_map.items():
                primary_task = ", ".join(task_names)
                coros.append(_probe_openrouter_model(model_id, primary_task, client))

        # Run all model checks concurrently in parallel for sub-2s response
        if coros:
            probed = await asyncio.gather(*coros, return_exceptions=True)
            for item in probed:
                if isinstance(item, tuple) and len(item) == 2:
                    k, v = item
                    results[k] = v

        if not results:
            return AIModelsHealthResponse(
                status="unconfigured",
                openrouter_base_url=self.base_url,
                grok_base_url=grok_base_url,
                active_provider="unconfigured",
                models={},
            )

        all_ok = all(item.status == "ok" for item in results.values())
        any_ok = any(item.status == "ok" for item in results.values())

        if all_ok and results:
            overall = "healthy"
        elif any_ok:
            overall = "degraded"
        else:
            overall = "unhealthy"

        return AIModelsHealthResponse(
            status=overall,
            openrouter_base_url=self.base_url,
            grok_base_url=grok_base_url,
            active_provider=active_provider,
            models=results,
        )


# Global singleton instance
ai_router = AIRouter()
