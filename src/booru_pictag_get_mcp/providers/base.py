"""Base booru provider + common helpers.

Ported from lib/booru/base.ts (strategy pattern). Enrichment for flat-tag
providers (Gelbooru/Rule34) uses the static tag_categories.json + keyword
classifier fallback, *no Supabase*.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from ..constants import provider_post_url
from .httpclient import http_get_json
from ..models import BooruPost, SearchOptions
from ..core.normalize import to_space
from ..core.tag_classifier import classify_tag
from .. import data as tags_data
from .transforms import (
    transform_aibooru_post,
    transform_e621_post,
    transform_gelbooru_post,
    transform_rule34_post,
)


VIDEO_RE = re.compile(r"\.(mp4|webm|avi|mov|mkv)$", re.IGNORECASE)


def _normalize_rating(r: str) -> str:
    r = (r or "").lower().strip()
    if r in ("s", "safe"):
        return "s"
    if r in ("q", "questionable"):
        return "q"
    if r in ("e", "explicit"):
        return "e"
    return r or "q"


def _is_valid_post_dict(p: Any) -> bool:
    if not isinstance(p, dict):
        return False
    file_url = p.get("file_url") or p.get("sample_url") or ""
    tag_string = p.get("tag_string") or p.get("tags") or ""
    return bool(
        file_url
        and isinstance(file_url, str)
        and "deleted" not in file_url
        and p.get("id")
        and tag_string
        and not VIDEO_RE.search(file_url)
    )


def _is_valid_post(bp: BooruPost) -> bool:
    """Filter on the already-built BooruPost.

    Empty/deleted/video file URLs are dropped. Posts without an id or any tag
    content are also discarded.
    """
    file_url = bp.file_url or bp.large_file_url or bp.preview_file_url
    if not file_url or not isinstance(file_url, str):
        return False
    if "deleted" in file_url:
        return False
    if not bp.id:
        return False
    if not (bp.tag_string or "").strip():
        return False
    if VIDEO_RE.search(file_url):
        return False
    return True


class BaseBooruProvider(ABC):
    provider: str = "base"
    base_url: str = ""

    async def search(self, options: SearchOptions) -> list[BooruPost]:
        url = self._build_search_url(options)
        raw = await http_get_json(url)
        # Some providers wrap posts under "post" key, others under "posts".
        if isinstance(raw, dict):
            posts_data = raw.get("post") or raw.get("posts") or raw
        else:
            posts_data = raw
        if not isinstance(posts_data, list):
            return []
        # Build BooruPost via the per-provider transform, then drop ones whose
        # file_url is empty/deleted/video — each provider can also fully
        # override _normalize if it needs richer filtering.
        posts: list[BooruPost] = []
        for p in posts_data:
            if not isinstance(p, dict):
                continue
            bp = self._to_booru_post(p)
            if not _is_valid_post(bp):
                continue
            posts.append(bp)
        return posts

    @abstractmethod
    def _build_search_url(self, options: SearchOptions) -> str: ...

    def _normalize(self, posts: list[dict]) -> list[BooruPost]:
        # Deprecated hook kept for subclasses overriding _to_booru_post only.
        return [self._to_booru_post(p) for p in posts if isinstance(p, dict)]

    def _to_booru_post(self, p: dict) -> BooruPost:
        # providers override
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
            rating=_normalize_rating(p.get("rating") or "q"),
            score=int(p.get("score") or 0),
            source=p.get("source"),
            width=int(p.get("image_width") or p.get("width") or 0),
            height=int(p.get("image_height") or p.get("height") or 0),
            provider=self.provider,
        )

    def _enrich_flat_post(self, post: BooruPost) -> BooruPost:
        """For flat-tag providers, classify each tag into artist/character/copyright.

        Uses tag_categories.json (Danbooru-derived dict); unknown tags fall back
        to keyword classification only for copyright/character-ish patterns.
        """
        cats = tags_data.load_tag_categories()
        artist_tags: list[str] = []
        char_tags: list[str] = []
        cpy_tags: list[str] = []
        meta_tags: list[str] = []
        for t_orig in (post.tag_string or "").split():
            t = t_orig.lower()
            cat = cats.get(t)
            if cat == 1:
                artist_tags.append(t)
            elif cat == 3:
                cpy_tags.append(t)
            elif cat == 4:
                char_tags.append(t)
            elif cat == 5:
                meta_tags.append(t)
        post.tag_string_artist = " ".join(artist_tags) if artist_tags else ""
        post.tag_string_character = " ".join(char_tags) if char_tags else ""
        post.tag_string_copyright = " ".join(cpy_tags) if cpy_tags else ""
        # leave tag_string_meta (clean pipeline drops meta via curated list anyway)
        return post


# ============================================================
# Concrete providers
# ============================================================

class DanbooruProvider(BaseBooruProvider):
    provider = "danbooru"
    base_url = "https://danbooru.donmai.us"

    ONLY_FIELDS = ("id,file_url,large_file_url,preview_file_url,tag_string,"
                   "tag_string_artist,tag_string_character,tag_string_copyright,"
                   "tag_string_meta,rating,image_width,image_height")

    def _build_search_url(self, o: SearchOptions) -> str:
        from urllib.parse import urlencode

        is_random = o.order == "random"
        tags = (o.tags or "").strip()
        if o.order == "recent":
            final_tags = tags
        elif is_random:
            ct = re.sub(r"order:random|random:\d+", "", tags, flags=re.I).strip() if tags else ""
            final_tags = f"{ct} random:30" if ct else "random:30"
        else:
            final_tags = f"{tags} order:rank" if tags else "order:rank"

        if o.rating == "safe":
            final_tags = (f"{final_tags} rating:general" if final_tags else "rating:general")

        params = {
            "limit": str(o.limit),
            "only": self.ONLY_FIELDS,
            "page": str(o.page),
            "tags": final_tags,
        }
        if is_random:
            params["_seed"] = f"{o.random_seed}_{o.page}"
        return f"{self.base_url}/posts.json?{urlencode(params)}"


class AibooruProvider(DanbooruProvider):
    provider = "aibooru"
    base_url = "https://aibooru.online"

    def _to_booru_post(self, p: dict) -> BooruPost:
        return transform_aibooru_post(p)


class E621Provider(BaseBooruProvider):
    provider = "e621"
    base_url = "https://e621.net"

    def _build_search_url(self, o: SearchOptions) -> str:
        from urllib.parse import urlencode

        tags = (o.tags or "").strip()
        # e621 supports order:score / order:favcount / order:random — NOT order:rank.
        if o.order == "popular":
            tags = f"{tags} order:score" if tags else "order:score"
        elif o.order == "random":
            tags = f"{tags} order:random" if tags else "order:random"
        if o.rating == "safe":
            tags = f"{tags} rating:s" if tags else "rating:s"
        params = {
            "limit": str(o.limit),
            "page": str(o.page),
            "tags": tags,
        }
        return f"{self.base_url}/posts.json?{urlencode(params)}"

    def _to_booru_post(self, p: dict) -> BooruPost:
        return transform_e621_post(p)


class GelbooruProvider(BaseBooruProvider):
    provider = "gelbooru"
    base_url = "https://gelbooru.com"

    def _build_search_url(self, o: SearchOptions) -> str:
        import os
        from urllib.parse import urlencode

        tags = (o.tags or "").strip()
        order_q = ""
        if o.order == "popular":
            order_q = " sort:score"
        elif o.order == "random":
            order_q = " sort:random"
        if o.rating == "safe":
            tags = f"{tags} rating:safe" if tags else "rating:safe"
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": "1",
            "limit": str(o.limit),
            "tags": f"{tags}{order_q}".strip(),
            "pid": str(o.page - 1),
        }
        # Gelbooru API key (user_id + api_key). Required since 2025-08.
        user_id = os.getenv("GELBOORU_USER_ID")
        api_key = os.getenv("GELBOORU_API_KEY")
        if user_id and api_key:
            params["user_id"] = user_id
            params["api_key"] = api_key
        return f"{self.base_url}/index.php?{urlencode(params)}"

    def _to_booru_post(self, p: dict) -> BooruPost:
        post = transform_gelbooru_post(p)
        return self._enrich_flat_post(post)


class Rule34Provider(BaseBooruProvider):
    provider = "rule34"
    base_url = "https://api.rule34.xxx"

    def _build_search_url(self, o: SearchOptions) -> str:
        import os
        from urllib.parse import urlencode

        tags = (o.tags or "").strip()
        # rule34 has no real popular order; recent = default; random via sort:random
        if o.order == "random":
            tags = f"{tags} sort:random" if tags else "sort:random"
        if o.rating == "safe":
            # rule34 has very few safe posts; we still filter
            tags = f"{tags} rating:safe" if tags else "rating:safe"
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": "1",
            "limit": str(o.limit),
            "tags": tags,
            "pid": str(o.page - 1),
        }
        # Rule34 API key. Required since 2025-08. Like Gelbooru, Rule34 needs BOTH
        # user_id and api_key (the URL you copied from the site is
        # `?api_key=...&user_id=...`).
        api_key = os.getenv("RULE34_API_KEY")
        user_id = os.getenv("RULE34_USER_ID")
        if api_key:
            params["api_key"] = api_key
        if user_id:
            params["user_id"] = user_id
        return f"{self.base_url}/index.php?{urlencode(params)}"

    def _to_booru_post(self, p: dict) -> BooruPost:
        post = transform_rule34_post(p)
        return self._enrich_flat_post(post)