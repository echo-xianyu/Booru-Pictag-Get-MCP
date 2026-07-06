"""booru-pictag-get-mcp server — exposes 4 MCP tools over stdio.

Tools:
  - search_prompts   : search + clean → ready-to-use prompts (one step)
  - build_prompt     : clean an already-provided tag set (no network)
  - search_posts     : raw post list (no cleaning)
  - autocomplete_tags: booru tag autocomplete (canonical tag form)
"""

from __future__ import annotations

import asyncio
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .models import (
    ProviderType, OrderType, RatingFilter,
    BooruPost, SearchOptions,
)
from .providers.factory import get_provider
from .providers.httpclient import http_get_json
from .core.clean_prompt import clean_prompt, CleanPromptOptions
from .core.background import BackgroundMode
from .constants import provider_post_url


mcp = FastMCP("booru-pictag-get-mcp")


def _clean_opts(
    include_characters: bool,
    include_copyrights: bool,
    optimize: bool,
    resolve_conflicts: bool,
    exclude: list[str],
    added_tags: list[str],
    background_mode: str,
    simple_replace: str | None,
) -> CleanPromptOptions:
    try:
        bg = BackgroundMode(background_mode)
    except ValueError:
        bg = BackgroundMode.KEEP
    return CleanPromptOptions(
        include_characters=include_characters,
        include_copyrights=include_copyrights,
        optimize=optimize,
        resolve_conflicts=resolve_conflicts,
        exclude=exclude or [],
        added_tags=added_tags or [],
        background_mode=bg,
        simple_background_replacement_tags=simple_replace,
    )


def _post_to_prompt_dict(
    post: BooruPost,
    opts: CleanPromptOptions,
    include_preview: bool,
) -> dict:
    cleaned = clean_prompt(
        post.tag_string,
        artist_tags=post.tag_string_artist,
        character_tags=post.tag_string_character,
        copyright_tags=post.tag_string_copyright,
        options=opts,
    )
    d: dict = {
        "id": post.id,
        "provider": post.provider,
        "rating": post.rating,
        "score": post.score,
        "post_url": provider_post_url(post.provider or "danbooru", post.id),
        "prompt": cleaned["prompt"],
        "categories": cleaned["categories"],
        "raw_tag_count": cleaned["raw_tag_count"],
    }
    if include_preview and post.preview_file_url:
        d["preview_url"] = post.preview_file_url
    if post.ai_metadata:
        am = post.ai_metadata
        if am.prompt:
            d["ai_prompt"] = am.prompt
        if am.negative_prompt:
            d["ai_negative_prompt"] = am.negative_prompt
        if am.model:
            d["ai_model"] = am.model
        if am.steps is not None:
            d["ai_steps"] = am.steps
        if am.cfg_scale is not None:
            d["ai_cfg_scale"] = am.cfg_scale
        if am.sampler:
            d["ai_sampler"] = am.sampler
        if am.seed is not None:
            d["ai_seed"] = am.seed
    return d


def _post_to_raw_dict(post: BooruPost, include_preview: bool,
                      include_file_url: bool) -> dict:
    d: dict = {
        "id": post.id,
        "provider": post.provider,
        "rating": post.rating,
        "score": post.score,
        "post_url": provider_post_url(post.provider or "danbooru", post.id),
        "raw_tags": post.tag_string,
        "artist_tags": post.tag_string_artist,
        "character_tags": post.tag_string_character,
        "copyright_tags": post.tag_string_copyright,
        "meta_tags": post.tag_string_meta,
    }
    if include_preview and post.preview_file_url:
        d["preview_url"] = post.preview_file_url
    if include_file_url:
        d["file_url"] = post.file_url
        d["large_file_url"] = post.large_file_url
    if post.ai_metadata and post.ai_metadata.prompt:
        d["ai_prompt"] = post.ai_metadata.prompt
        if post.ai_metadata.model:
            d["ai_model"] = post.ai_metadata.model
    return d


@mcp.tool(
    description=(
        "Search an image booru (Danbooru/AIBooru/e621/Gelbooru/Rule34) by TAG and "
        "return ready-to-use, cleaned AI-art prompts. Each result has the full "
        "prompt string plus its category split (appearance/clothing/pose/scenery/"
        "character/quality/other). This is the recommended tool for finding "
        "'ready-to-use AI painting tags'.\n"
        "\n"
        "== SEARCH SEMANTICS — read this before calling ==\n"
        "- This is NOT a keyword-search engine like Google. You query with one or "
        "more booru TAGS, and results are images ALL of whose tags are present.\n"
        "- A booru tag is a single token, multi-word tags use UNDERSCORE: "
        "'blue_hair', 'hatsune_miku', 'sitting_on_chair' — never 'blue hair'.\n"
        "- STRONGLY PREFER A SINGLE TAG to start. 'hatsune_miku' returns "
        "thousands of well-tagged images; 'hatsune_miku blue_hair school_uniform "
        "smile' is treated as AND → dramatically fewer results (often zero). The "
        "cleaned prompt already contains far more detail than your search tag, "
        "so adding search tags is at best redundant and at worst returns nothing.\n"
        "- When you need a pure-quality / generalized set (no specific character "
        "or franchise yet), search '1girl' or '1boy' alone, or use 'random' order.\n"
        "- Do not write natural-language queries ('a girl with blue hair sitting "
        "in a classroom') — that is not supported. Translate to booru tags first.\n"
        "- Use `autocomplete_tags` if you are not sure how a concept is spelled "
        "as a booru tag (e.g. user said '法国女仆' → try 'french', 'maid' and let "
        "autocomplete return 'french maid', 'maid_uniform', etc.).\n"
        "- Common useful single-tag starting points: a character tag "
        "('hatsune_miku'), an artist tag, a copyright tag ('blue_archive'), a "
        "character + single qualifier ('2girls' for group shots), or 'order:rank' "
        "/ 'random' for non-themed browsing via `order` param."
    ),
)
async def search_prompts(
    tags: str,
    provider: ProviderType = "danbooru",
    order: OrderType = "popular",
    page: int = 1,
    limit: int = 30,
    rating: RatingFilter = "all",
    random_seed: int = 1,
    include_characters: bool = True,
    include_copyrights: bool = True,
    optimize: bool = True,
    resolve_conflicts: bool = False,  # Deprecated: kept for forward-compat. Defaults off because conflict rules assume a single subject — turning on would mangle multi-character prompts (1girl+1boy, smile+crying, long_hair+short_hair).
    exclude: Optional[list[str]] = None,
    added_tags: Optional[list[str]] = None,
    background_mode: str = "keep",
    simple_background_replacement_tags: Optional[str] = None,
    min_tag_count: int = 0,
    include_preview: bool = False,
) -> dict:
    """Search and clean in one go.

    Typical usage:
        tags='hatsune_miku'                         → 30 cleaned prompts of her,
                                                       each already a full ready prompt
        tags='blue_archive' order='popular'          → fan-art prompts
        tags='' order='random' rating='safe'        → random safe posts, varied

    Avoid: tags='hatsune_miku blue_hair smile school_uniform' (too AND-heavy,
    usually returns 0). Use a single tag and let the prompt-cleaner enrich it.
    """
    opts = _clean_opts(
        include_characters, include_copyrights, optimize, resolve_conflicts,
        exclude or [], added_tags or [], background_mode, simple_background_replacement_tags,
    )
    o = SearchOptions(
        tags=tags or "",
        page=max(1, int(page)),
        limit=max(1, min(int(limit), 100)),
        order=order,  # type: ignore[arg-type]
        rating=rating,  # type: ignore[arg-type]
        random_seed=int(random_seed),
    )
    provider_obj = get_provider(provider)
    posts = await provider_obj.search(o)

    out_posts = []
    dropped = 0
    for p in posts:
        if min_tag_count and len((p.tag_string or "").split()) < min_tag_count:
            dropped += 1
            continue
        out_posts.append(_post_to_prompt_dict(p, opts, include_preview))

    return {
        "provider": provider,
        "order": order,
        "tags": tags,
        "page": o.page,
        "limit": o.limit,
        "total": len(out_posts),
        "dropped_below_min": dropped,
        "posts": out_posts,
    }


@mcp.tool(
    description=(
        "Clean an already-known set of booru tags into a ready-to-use prompt. "
        "Use this when you already have a tag list (e.g. user pasted one or "
        "you received raw tags from `search_posts`) and only want the cleaned "
        "output. No network request is made.\n"
        "\n"
        "`tag_string` accepts the SAME raw booru format that `search_posts` "
        "returns in `raw_tags`: space-separated, multi-word tags joined by "
        "UNDERSCORE ('1girl long_hair blue_eyes smile'). It also accepts a "
        "comma-separated list of already-cleaned tags ('1girl, long hair, blue "
        "eyes, smile') for idempotent re-cleaning. Do NOT pass natural-language "
        "sentences — split them into booru tags first (use "
        "`autocomplete_tags` to find the canonical form of each)."
    ),
)
async def build_prompt(
    tag_string: str,
    artist_tags: str = "",
    character_tags: str = "",
    copyright_tags: str = "",
    meta_tags: str = "",
    include_characters: bool = True,
    include_copyrights: bool = True,
    optimize: bool = True,
    resolve_conflicts: bool = False,  # Deprecated: see search_prompts note.
    exclude: Optional[list[str]] = None,
    added_tags: Optional[list[str]] = None,
    background_mode: str = "keep",
    simple_background_replacement_tags: Optional[str] = None,
) -> dict:
    """No-network tag cleaning. See `search_prompts` for tag formats."""
    opts = _clean_opts(
        include_characters, include_copyrights, optimize, resolve_conflicts,
        exclude or [], added_tags or [], background_mode, simple_background_replacement_tags,
    )
    opts.meta_tags = meta_tags
    out = clean_prompt(
        tag_string,
        artist_tags=artist_tags,
        character_tags=character_tags,
        copyright_tags=copyright_tags,
        options=opts,
    )
    return {
        "prompt": out["prompt"],
        "categories": out["categories"],
        "raw_tag_count": out["raw_tag_count"],
    }


@mcp.tool(
    description=(
        "Search a booru and return the raw post list (no cleaning). The same "
        "search semantics as `search_prompts` apply:\n"
        "- Query with one or more booru TAGs (underscores for multi-word: "
        "'blue_hair', 'hatsune_miku'), never write natural language.\n"
        "- Tags AND together — every tag must be present in each returned post. "
        "PREFER A SINGLE TAG; stacking tags usually returns 0 posts. The "
        "cleaned prompt is where 'more detail' lives, not in the search query.\n"
        "- When unsure how a concept is tagged, call `autocomplete_tags` first.\n"
        "Use this tool when you want to inspect the original tags before "
        "deciding how to process them. Each post carries its raw tag_string, "
        "the artist/character/copyright splits (when available), and optionally "
        "preview/file URLs."
    ),
)
async def search_posts(
    tags: str,
    provider: ProviderType = "danbooru",
    order: OrderType = "popular",
    page: int = 1,
    limit: int = 30,
    rating: RatingFilter = "all",
    random_seed: int = 1,
    include_preview: bool = True,
    include_file_url: bool = False,
) -> dict:
    """Raw post list, no cleaning. See `search_prompts` for tag semantics."""
    o = SearchOptions(
        tags=tags or "",
        page=max(1, int(page)),
        limit=max(1, min(int(limit), 100)),
        order=order,  # type: ignore[arg-type]
        rating=rating,  # type: ignore[arg-type]
        random_seed=int(random_seed),
    )
    provider_obj = get_provider(provider)
    posts = await provider_obj.search(o)
    return {
        "provider": provider,
        "order": order,
        "tags": tags,
        "page": o.page,
        "limit": o.limit,
        "total": len(posts),
        "posts": [_post_to_raw_dict(p, include_preview, include_file_url) for p in posts],
    }


@mcp.tool(
    description=(
        "Autocomplete a tag fragment against the booru tag index, returning the "
        "canonical tag name with its post count and category. Use this to turn "
        "a natural word or partial fragment into the exact booru tag form before "
        "calling the search tools:\n"
        "  user says       → autocomplete query    → pick returned `name`\n"
        "  'blue hair'     → 'blue hair' or 'blue'  → 'blue_hair'\n"
        "  'miku'          → 'miku'                 → 'hatsune_miku' (or other)\n"
        "  'knight'        → 'knight'               → 'knight', 'female_knight', ...\n"
        "\n"
        "Behavior:\n"
        "- You do NOT need to add a trailing '*'; the tool appends it for you.\n"
        "- Multi-word fragments are allowed (passed verbatim, e.g. 'long "
        "skirt'). Returns tags whose `name` starts with the fragment in some "
        "ordering (Danbooru matches the whole underscore-joined form).\n"
        "- `post_count` lets you reject obscure tags (likely to return ~0 "
        "results in `search_prompts`). Prefer tags with post_count > 100.\n"
        "- category: 0=general, 1=artist, 3=copyright, 4=character, 5=meta — use "
        "this to choose between, e.g. 'blue_archive' (3, copyright) vs an artist "
        "named 'blue_archive' (1).\n"
        "- Always uses Danbooru (or AIBooru) for tag indexes since they have the "
        "most complete data; `provider` only accepts those two values here. For "
        "Rule34/Gelbooru/e621 search use `search_prompts`/`search_posts` with "
        "the tag name you found here (booru tags are largely cross-compatible)."
    ),
)
async def autocomplete_tags(
    query: str,
    provider: ProviderType = "danbooru",
    limit: int = 10,
) -> dict:
    """Tag autocomplete via tags.json search[name_matches]=<query>*.

    Run this BEFORE `search_prompts`/`search_posts` if the user's request was in
    natural language or you're unsure whether a concept exists as a single tag.
    """
    base = {
        "danbooru": "https://danbooru.donmai.us",
        "aibooru": "https://aibooru.online",
    }.get(provider, "https://danbooru.donmai.us")
    n = max(1, min(int(limit), 50))
    if not query:
        return {"query": query, "tags": []}
    q = query.strip()
    if "*" not in q:
        q = f"{q}*"
    from urllib.parse import urlencode
    params = {
        "search[name_matches]": q,
        "search[order]": "count",
        "limit": str(n),
    }
    url = f"{base}/tags.json?{urlencode(params)}"
    raw = await http_get_json(url)
    if not isinstance(raw, list):
        return {"query": query, "tags": []}
    out_tags = [
        {
            "name": t.get("name", ""),
            "post_count": int(t.get("post_count") or 0),
            "category": int(t.get("category") or 0),
        }
        for t in raw if isinstance(t, dict) and t.get("name")
    ]
    return {"query": query, "provider": provider, "tags": out_tags}


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()