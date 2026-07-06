"""Centralized constants for the Booru Tag Search MCP.

Ported from lib/constants.ts of booru-prompt-gallery (MIT, Mexes-GM).
Supabase/Sentry/Netlify/Vercel constants removed as irrelevant.
"""

from __future__ import annotations

# Provider base URLs
PROVIDER_URLS = {
    "danbooru": "https://danbooru.donmai.us",
    "aibooru": "https://aibooru.online",
    "rule34": "https://api.rule34.xxx",
    "rule34_web": "https://rule34.xxx",
    "e621": "https://e621.net",
    "e926": "https://e926.net",
    "gelbooru": "https://gelbooru.com",
}


def provider_post_url(provider: str, post_id: int | str) -> str:
    p = (provider or "").lower()
    pid = str(post_id)
    if p == "danbooru":
        return f"{PROVIDER_URLS['danbooru']}/posts/{pid}"
    if p == "aibooru":
        return f"{PROVIDER_URLS['aibooru']}/posts/{pid}"
    if p == "rule34":
        return f"{PROVIDER_URLS['rule34_web']}/index.php?page=post&s=view&id={pid}"
    if p == "e621":
        return f"{PROVIDER_URLS['e621']}/posts/{pid}"
    if p == "gelbooru":
        return f"{PROVIDER_URLS['gelbooru']}/index.php?page=post&s=view&id={pid}"
    return f"{PROVIDER_URLS['danbooru']}/posts/{pid}"


def get_provider_search_url(provider: str, tag: str) -> str:
    p = (provider or "").lower()
    from urllib.parse import quote

    enc = quote(tag)
    base = {
        "danbooru": f"{PROVIDER_URLS['danbooru']}/posts?tags={enc}",
        "aibooru": f"{PROVIDER_URLS['aibooru']}/posts?tags={enc}",
        "rule34": f"{PROVIDER_URLS['rule34_web']}/index.php?page=post&s=list&tags={enc}",
        "e621": f"{PROVIDER_URLS['e621']}/posts?tags={enc}",
        "gelbooru": f"{PROVIDER_URLS['gelbooru']}/index.php?page=post&s=list&tags={enc}",
    }
    return base.get(p, base["danbooru"])


USER_AGENT = "BooruTagSearchMCP/1.0"


def get_danbooru_user_agent() -> str:
    """Danbooru prefers a User-Agent identifying the account. Optional."""
    import os

    username = os.getenv("DANBOORU_USERNAME", "")
    return f"BooruTagSearchMCP/1.0 (Danbooru user: {username})" if username else "BooruTagSearchMCP/1.0"


DEFAULT_BLACKLIST = ["guro", "scat"]