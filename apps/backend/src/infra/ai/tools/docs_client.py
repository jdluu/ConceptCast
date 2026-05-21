"""Context7 API client for fetching documentation context.

Uses the Context7 REST API (https://context7.com/docs/api-guide) to retrieve
relevant docs. Manim Community is available as library ID
/websites/manim_community_en_stable.
Adds lightweight in-memory caching and retry/backoff for reliability.
"""

import asyncio
import json
import random
import time
from collections import OrderedDict

import httpx

from infra.settings import get_settings

CONTEXT7_BASE = "https://context7.com/api/v2"
MANIM_COMMUNITY_LIBRARY_ID = "/websites/manim_community_en_stable"
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

_CTX7_CACHE: OrderedDict[str, tuple[float, str]] = OrderedDict()


def _cache_key(query: str, api_key: str) -> str:
    """Generates a stable cache key for a given query and identity."""
    return f"{api_key}:{query.strip().lower()}"


def _format_docs_payload(data: object) -> str:
    if not data or not isinstance(data, list):
        return "No documentation matches. Use standard Manim Community syntax."
    parts: list[str] = []
    for item in data:
        if isinstance(item, dict):
            title = item.get("title") or "Documentation"
            content = item.get("content") or ""
            source = item.get("source") or ""
            if content:
                parts.append(
                    f"### {title}\n{content}\nSource: {source}"
                    if source
                    else f"### {title}\n{content}"
                )
    if not parts:
        return "No documentation matches. Use standard Manim Community syntax."
    return "\n\n---\n\n".join(parts)


def _set_cache_entry(key: str, value: str, ttl_seconds: int, max_entries: int) -> None:
    """Sets/updates a cache entry and enforces LRU maximum cache size."""
    if ttl_seconds <= 0 or max_entries <= 0:
        return

    now = time.time()
    # Opportunistically clean expired entries first.
    expired_keys = [
        k for k, (expires_at, _) in _CTX7_CACHE.items() if expires_at <= now
    ]
    for k in expired_keys:
        _CTX7_CACHE.pop(k, None)

    if key in _CTX7_CACHE:
        _CTX7_CACHE.pop(key, None)
    _CTX7_CACHE[key] = (now + ttl_seconds, value)
    _CTX7_CACHE.move_to_end(key, last=True)

    # LRU eviction: remove oldest (least recently used).
    while len(_CTX7_CACHE) > max_entries:
        oldest_key = next(iter(_CTX7_CACHE))
        _CTX7_CACHE.pop(oldest_key, None)


def _get_cache_entry(key: str) -> str | None:
    """Returns cached value if present and not expired; refreshes LRU order on hit."""
    cached = _CTX7_CACHE.get(key)
    if not cached:
        return None
    expires_at, value = cached
    if expires_at <= time.time():
        _CTX7_CACHE.pop(key, None)
        return None
    _CTX7_CACHE.move_to_end(key, last=True)
    return value


def _compute_backoff_delay(
    *, attempt: int, base_seconds: float, retry_after_header: str | None
) -> float:
    """Backoff with jitter, honoring Retry-After when present."""
    if retry_after_header:
        try:
            retry_after = float(retry_after_header)
            if retry_after > 0:
                return retry_after
        except ValueError:
            pass
    # Exponential backoff + small jitter spread.
    exp_delay = base_seconds * (2**attempt)
    jitter = random.uniform(0.0, 0.25)  # noqa: S311
    return exp_delay + jitter  # type: ignore


async def get_manim_docs_context(query: str, *, api_key: str) -> str:  # noqa: PLR0911
    """Retrieves Manim Community documentation snippets from Context7.

    Fetches relevant snippets based on the provided query, applying caching
    and automated retries for transient network issues.

    Args:
        query: Descriptive term or question for documentation retrieval.
        api_key: Authorized Context7 API key.

    Returns:
        A formatted string of relevant snippets, or a safe fallback message.
    """
    settings = get_settings()
    cache_ttl = max(0, getattr(settings, "context7_cache_ttl_seconds", 1800))
    max_retries = max(0, getattr(settings, "context7_max_retries", 2))
    cache_max_entries = max(0, getattr(settings, "context7_cache_max_entries", 256))

    cache_key = _cache_key(query, api_key)
    cached = _get_cache_entry(cache_key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "libraryId": MANIM_COMMUNITY_LIBRARY_ID,
        "query": query,
    }
    base_backoff_seconds = 0.5
    last_error = "Context7 request failed"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.get(
                    f"{CONTEXT7_BASE}/context",
                    headers=headers,
                    params=params,
                )
            except httpx.InvalidURL as e:
                return f"Context7 request error (invalid url): {e}. Query may be too long. Use standard Manim Community syntax."
            except (httpx.RequestError, Exception) as e:
                last_error = f"Context7 request error: {e}"
                if attempt < max_retries:
                    await asyncio.sleep(
                        _compute_backoff_delay(
                            attempt=attempt,
                            base_seconds=base_backoff_seconds,
                            retry_after_header=None,
                        )
                    )
                    continue
                return f"{last_error}. Use standard Manim Community syntax."

            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    result = (
                        response.text
                        or "No documentation matches. "
                        "Use standard Manim Community syntax."
                    )
                    _set_cache_entry(
                        cache_key,
                        result,
                        ttl_seconds=cache_ttl,
                        max_entries=cache_max_entries,
                    )
                    return result

                result = _format_docs_payload(data)
                _set_cache_entry(
                    cache_key,
                    result,
                    ttl_seconds=cache_ttl,
                    max_entries=cache_max_entries,
                )
                return result

            if (
                response.status_code in _TRANSIENT_STATUS_CODES
                and attempt < max_retries
            ):
                await asyncio.sleep(
                    _compute_backoff_delay(
                        attempt=attempt,
                        base_seconds=base_backoff_seconds,
                        retry_after_header=response.headers.get("Retry-After"),
                    )
                )
                continue

            return (
                f"Context7 API error ({response.status_code}). "
                "Use standard Manim Community syntax."
            )

    return f"{last_error}. Use standard Manim Community syntax."
