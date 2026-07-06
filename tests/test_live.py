"""Manual end-to-end test against the real booru APIs.

Run a small <tags> search through every provider, then a search_prompts round
through Danbooru + AIBooru. Requires network.

Usage:
    python tests/test_live.py [tag] [provider]
    python tests/test_live.py hatsune_miku                  # default tag, all providers
    python tests/test_live.py hatsune_miku gelbooru         # single provider
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from booru_pictag_get_mcp.models import SearchOptions
from booru_pictag_get_mcp.providers.factory import get_provider
from booru_pictag_get_mcp.core.clean_prompt import clean_prompt, CleanPromptOptions
from booru_pictag_get_mcp.constants import provider_post_url


def _summarize(post):
    return {
        "id": post.id,
        "rating": post.rating,
        "score": post.score,
        "preview": post.preview_file_url[:60] + "..." if post.preview_file_url else "",
        "tag_count": len((post.tag_string or "").split()),
        "char": post.tag_string_character,
        "cpy": post.tag_string_copyright,
        "artist": post.tag_string_artist,
        "ai": post.ai_metadata.prompt[:80] if (post.ai_metadata and post.ai_metadata.prompt) else None,
    }


async def test_provider(tag: str, name: str):
    print(f"\n=== {name.upper()} ({tag!r}) ===")
    p = get_provider(name)
    o = SearchOptions(tags=tag, order="popular", limit=3, random_seed=1)
    try:
        posts = await p.search(o)
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return
    print(f"  returned {len(posts)} posts")
    for pi, post in enumerate(posts):
        print(f"  [{pi}] {_summarize(post)}")
        if not posts:
            continue
    return posts


async def search_prompts_demo(tag: str, provider: str):
    print(f"\n--- search_prompts demo [{provider}] ---")
    p = get_provider(provider)
    o = SearchOptions(tags=tag, order="popular", limit=3, random_seed=1)
    posts = await p.search(o)
    for pi, post in enumerate(posts):
        out = clean_prompt(
            post.tag_string,
            artist_tags=post.tag_string_artist,
            character_tags=post.tag_string_character,
            copyright_tags=post.tag_string_copyright,
            options=CleanPromptOptions(),
        )
        print(f"\n  [{pi}] post {post.id} (rating={post.rating})")
        print(f"      prompt: {out['prompt']}")
        print(f"      cats  : {out['categories']}")


async def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "hatsune_miku"
    only = sys.argv[2] if len(sys.argv) > 2 else None
    providers = [only] if only else ["danbooru", "aibooru", "e621", "gelbooru", "rule34"]
    for name in providers:
        await test_provider(tag, name)
    if not only:
        await search_prompts_demo(tag, "danbooru")
        await search_prompts_demo(tag, "aibooru")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())