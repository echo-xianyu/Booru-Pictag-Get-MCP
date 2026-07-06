"""Post-shape transformers, ported from lib/booru/post-transformers.ts."""

from __future__ import annotations

from typing import Any

from ..models import BooruPost, AiMetadata


def transform_aibooru_post(p: Any) -> BooruPost:
    if not isinstance(p, dict):
        raise ValueError("Invalid post data from Aibooru")
    return BooruPost(
        id=int(p.get("id") or 0),
        file_url=p.get("file_url") or "",
        large_file_url=p.get("large_file_url") or p.get("file_url") or "",
        preview_file_url=p.get("preview_file_url") or p.get("file_url") or "",
        tag_string=p.get("tag_string") or "",
        tag_string_artist=p.get("tag_string_artist") or "",
        tag_string_character=p.get("tag_string_character") or "",
        tag_string_copyright=p.get("tag_string_copyright") or "",
        tag_string_meta=p.get("tag_string_meta") or "",
        rating=p.get("rating") or "q",
        score=int(p.get("score") or 0),
        source=p.get("source"),
        width=int(p.get("image_width") or p.get("width") or 0),
        height=int(p.get("image_height") or p.get("height") or 0),
        provider="aibooru",
        ai_metadata=AiMetadata(**(p.get("ai_metadata") or {}) if isinstance(p.get("ai_metadata"), dict) else {}) or None,
    )


def _ai_meta_from_emap(d: Any) -> AiMetadata | None:
    if not isinstance(d, dict):
        return None
    fields = {}
    for k in ("prompt", "negative_prompt", "model", "sampler"):
        if k in d:
            fields[k] = d[k]
    for k in ("steps", "cfg_scale", "seed"):
        if k in d:
            try:
                fields[k] = d[k]
            except Exception:
                pass
    if not fields:
        return None
    return AiMetadata(**fields)


def transform_e621_post(p: Any) -> BooruPost:
    if not isinstance(p, dict):
        raise ValueError("Invalid post data from E621")
    file = p.get("file") or {}
    sample = p.get("sample") or {}
    preview = p.get("preview") or {}
    tags = p.get("tags") or {}
    score = p.get("score") or {}

    content_cats = ["general", "species", "character", "copyright", "artist", "lore"]
    all_tags: list[str] = []
    for cat in content_cats:
        arr = tags.get(cat)
        if isinstance(arr, list):
            all_tags += arr

    return BooruPost(
        id=int(p.get("id") or 0),
        file_url=file.get("url") or "",
        large_file_url=sample.get("url") or file.get("url") or "",
        preview_file_url=preview.get("url") or file.get("url") or "",
        tag_string=" ".join(all_tags),
        tag_string_artist=" ".join(tags.get("artist") or []),
        tag_string_character=" ".join(tags.get("character") or []),
        tag_string_copyright=" ".join(tags.get("copyright") or []),
        rating=p.get("rating") or "q",
        score=int(score.get("total") or 0) if isinstance(score, dict) else int(score or 0),
        width=int(file.get("width") or 0),
        height=int(file.get("height") or 0),
        provider="e621",
    )


def transform_gelbooru_post(p: Any) -> BooruPost:
    """Gelbooru dapi JSON returns post props under post-record (root array or {post:[...]})."""
    if not isinstance(p, dict):
        raise ValueError("Invalid post data from Gelbooru")
    # Gelbooru stores post fields at top level.
    id = int(p.get("id") or 0)
    file_url = p.get("file_url") or ""
    sample = p.get("sample_url") or file_url or ""
    preview = p.get("preview_url") or p.get("preview_file_url") or file_url or ""
    tags = p.get("tags") or ""
    # Gelbooru tags are space-separated in underscore form
    rating = (p.get("rating") or "q")
    # Normalize rating to single-letter convention
    if rating in ("safe",):
        rating = "s"
    elif rating in ("questionable",):
        rating = "q"
    elif rating in ("explicit",):
        rating = "e"
    return BooruPost(
        id=id,
        file_url=file_url,
        large_file_url=sample,
        preview_file_url=preview,
        tag_string=tags,
        rating=rating,
        score=int(p.get("score") or 0),
        width=int(p.get("width") or 0),
        height=int(p.get("height") or 0),
        source=p.get("source"),
        provider="gelbooru",
    )


def transform_rule34_post(p: Any) -> BooruPost:
    if not isinstance(p, dict):
        raise ValueError("Invalid post data from Rule34")
    tags = p.get("tags") or ""
    rating = (p.get("rating") or "q")
    if rating in ("safe",):
        rating = "s"
    elif rating in ("questionable",):
        rating = "q"
    elif rating in ("explicit",):
        rating = "e"
    return BooruPost(
        id=int(p.get("id") or 0),
        file_url=p.get("file_url") or "",
        large_file_url=p.get("sample_url") or p.get("file_url") or "",
        preview_file_url=p.get("preview_url") or p.get("sample_url") or p.get("file_url") or "",
        tag_string=tags,
        rating=rating,
        score=int(p.get("score") or 0),
        width=int(p.get("width") or 0),
        height=int(p.get("height") or 0),
        source=p.get("source"),
        provider="rule34",
    )