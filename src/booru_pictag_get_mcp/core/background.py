"""Background tag processing — ported from lib/background-detector.ts.

v1 implements KEEP / REMOVE / REPLACE / SIMPLE_RANDOM / DETAILED_RANDOM with
text-only randomization (no image color sampling — kept lightweight for MCP).
Color sampling is a future enhancement behind the `pillow` optional extra.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional


class BackgroundMode(str, Enum):
    KEEP = "keep"
    REMOVE = "remove"
    REPLACE = "replace"
    SIMPLE_RANDOM = "simple_random"
    DETAILED_RANDOM = "detailed_random"


# Background-tag keywords for detection (subset; the TS version has richer lists).
SIMPLE_BG_KEYWORDS = [
    "simple background", "white background", "black background", "red background",
    "blue background", "green background", "yellow background", "orange background",
    "pink background", "purple background", "grey background", "gray background",
    "brown background", "beige background", "cream background", "abstract background",
    "plain background", "minimal background", "clean background", "empty background",
    "neutral background", "pastel background", "dark background", "light background",
    "vibrant background", "soft background", "blurred background", "bokeh background",
    "gradient background", "solid color", "monochrome", "two-tone background",
    "geometric background", "pattern background", "texture background",
    "gradient", "solid color background", "transparent background",
]

DETAILED_BG_KEYWORDS = [
    "indoors", "outdoors", "background", "scenery", "landscape",
    "sky", "cityscape", "forest", "beach", "mountain", "ocean", "room",
    "bedroom", "classroom", "living room", "bathroom", "kitchen",
    "night", "day", "sunset", "sunrise", "rain", "snow", "stars",
    "window", "wall", "floor", "ceiling",
]

# A minimal curated simple-color palette (text form, spacing-matched)
SIMPLE_RANDOM_POOL = [
    "simple background", "white background", "black background",
    "soft pastel background", "gradient background",
    "dark background", "light background",
]

# Curated detailed background scenes (each a small tag set)
DETAILED_RANDOM_POOL = [
    ["white background", "clean background"],
    ["simple background", "gradient background"],
    ["blue background", "light background"],
    ["black background", "dark background"],
    ["pink background", "soft background"],
    ["transparent background"],
    ["outdoors", "sky", "day", "blue sky", "cloud", "scenery"],
    ["outdoors", "sky", "sunset", "scenery"],
    ["outdoors", "night", "sky", "stars", "scenery"],
    ["forest", "outdoors", "tree", "scenery"],
    ["beach", "outdoors", "ocean", "sky", "scenery"],
    ["indoors", "room", "window", "sunlight"],
    ["indoors", "bedroom", "night"],
    ["indoors", "classroom", "after school"],
    ["cityscape", "outdoors", "night", "city lights"],
    ["cafe", "indoors", "window", "cozy"],
]


def _is_background_tag(tag: str) -> bool:
    t = tag.lower()
    for kw in SIMPLE_BG_KEYWORDS + DETAILED_BG_KEYWORDS:
        if kw in t:
            return True
    return t.endswith(" background")


def process_background_tags(
    tags: list[str],
    mode: BackgroundMode = BackgroundMode.KEEP,
    replacement_tags: Optional[str] = None,
    tag_overrides: Optional[dict] = None,
    random_patterns: bool = True,
    include_gradients: bool = False,
    detailed_list: Optional[list[list[str]]] = None,
    seed: Optional[int] = None,
) -> list[str]:
    """Apply the given background mode to a list of (already classified) tags."""
    if mode == BackgroundMode.KEEP:
        return tags

    rng = random.Random(seed)

    if mode == BackgroundMode.REMOVE:
        return [t for t in tags if not _is_background_tag(t)]

    if mode == BackgroundMode.REPLACE:
        repl_tags = [s.strip() for s in (replacement_tags or "").split(",") if s.strip()]
        stripped = [t for t in tags if not _is_background_tag(t)]
        # Append replacement tags at end (dedup)
        out = list(stripped)
        for r in repl_tags:
            if r not in out:
                out.append(r)
        return out

    if mode == BackgroundMode.SIMPLE_RANDOM:
        stripped = [t for t in tags if not _is_background_tag(t)]
        # Just pick a simple background from pool
        choice = rng.choice(SIMPLE_RANDOM_POOL)
        out = list(stripped)
        if choice not in out:
            out.append(choice)
        return out

    if mode == BackgroundMode.DETAILED_RANDOM:
        pool = detailed_list or DETAILED_RANDOM_POOL
        stripped = [t for t in tags if not _is_background_tag(t)]
        scene = rng.choice(pool)
        out = list(stripped)
        for s in scene:
            if s not in out:
                out.append(s)
        return out

    return tags