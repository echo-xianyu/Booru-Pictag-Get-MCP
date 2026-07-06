"""One-shot script: dump Danbooru tags into data/tag_categories.json.

Builds a static {name: category_int} dictionary used by Gelbooru/Rule34
providers (which return flat tag strings) to classify tags without Supabase.

Run once during build:
    python scripts/dump_tag_categories.py

Pulls pages of https://danbooru.donmai.us/tags.json ordered by post_count,
keeping only tags with post_count > 100 to keep the file small (~3 MB).
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

DANBOORU = "https://danbooru.donmai.us"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "tag_categories.json"

# Category integers on Danbooru: 0 general, 1 artist, 3 copyright, 4 character, 5 meta


def main() -> None:
    out: dict[str, int] = {}
    page = 1
    page_limit = 1000
    with httpx.Client(
        base_url=DANBOORU,
        headers={"User-Agent": "BooruTagSearchMCP/1.0 (dump)"},
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        while True:
            params = {
                "limit": "200",
                "page": str(page),
                "search[order]": "count",
                "search[hide_empty]": "yes",
            }
            r = client.get("/tags.json", params=params)
            r.raise_for_status()
            items = r.json()
            if not items:
                break
            kept = 0
            for it in items:
                pc = int(it.get("post_count", 0) or 0)
                if pc <= 100:
                    continue
                name = it.get("name", "").strip()
                if not name:
                    continue
                cat = int(it.get("category", 0) or 0)
                out[name] = cat
                kept += 1
            page += 1
            print(f"page {page-1}: +{kept} (total {len(out)})")
            if page > page_limit:
                break
            if len(items) < 200:
                break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), ), encoding="utf-8")
    print(f"wrote {len(out)} tags to {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()