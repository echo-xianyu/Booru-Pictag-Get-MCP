"""HTTP client with retries, timeout, and optional Danbooru Basic Auth."""

from __future__ import annotations

import asyncio
import base64
import os
import time
from typing import Optional

import httpx

from ..constants import USER_AGENT, get_danbooru_user_agent


def _auth_headers(for_url: str) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    is_danbooru = "danbooru.donmai.us" in for_url or for_url.endswith("/posts.json")
    if "danbooru.donmai.us" in for_url:
        headers["User-Agent"] = get_danbooru_user_agent()
        username = os.getenv("DANBOORU_USERNAME")
        apikey = os.getenv("DANBOORU_API_KEY")
        # Also accept combined form BOORU_DANBOORU_AUTH=user:key
        combined = os.getenv("DANBOORU_USERNAME_APIKEY")
        if combined and not (username and apikey) and ":" in combined:
            username, apikey = combined.split(":", 1)
        if username and apikey:
            cred = base64.b64encode(f"{username}:{apikey}".encode()).decode()
            headers["Authorization"] = f"Basic {cred}"
    else:
        headers["User-Agent"] = USER_AGENT
    return headers


async def http_get_json(url: str, *, retries: int = 2, timeout: float = 15.0) -> object:
    """Async GET returning parsed JSON. Empty body -> [].

    Uses HTTP/2 when available — required for some providers (e621) whose TLS
    stack frequently errors out on HTTP/1.1 keep-alive. Includes simple
    exponential-backoff retries on transient errors.
    """
    headers = _auth_headers(url)
    last_exc: Optional[Exception] = None
    # h2 is an optional dep; fall back to HTTP/1.1 if not installed.
    try:
        import h2  # noqa: F401
        use_http2 = True
    except ImportError:
        use_http2 = False
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                http2=use_http2,
            ) as client:
                r = await client.get(url)
            if r.status_code in (429,) or 500 <= r.status_code < 600:
                raise httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
            r.raise_for_status()
            text = r.text or ""
            if not text.strip():
                return []
            return r.json()
        except Exception as e:
            last_exc = e
            if attempt < retries:
                await asyncio.sleep(min(0.5 * (2 ** attempt), 3.0))
                continue
            raise
    if last_exc:
        raise last_exc
    return []