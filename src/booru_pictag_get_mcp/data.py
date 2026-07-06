"""Static tag-category dictionary loader for Gelbooru/Rule34 enrichment.

Tries (in order):
  1. importlib.resources bundled copy `booru_pictag_get_mcp/data/tag_categories.json`
  2. project-root `data/tag_categories.json`  (dev mode)
  3. empty dict  (graceful fallback; only keyword-based classification is used)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from importlib import resources

_CACHE: dict[str, int] | None = None


def load_tag_categories() -> dict[str, int]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    # 1. packaged copy
    try:
        with resources.files("booru_pictag_get_mcp.data").joinpath("tag_categories.json").open("rb") as f:
            _CACHE = json.load(f)
            return _CACHE
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        pass

    # 2. dev copy: <project_root>/data/tag_categories.json
    proj = Path(__file__).resolve().parents[4]
    cand = proj / "data" / "tag_categories.json"
    if cand.exists():
        with cand.open("rb") as f:
            _CACHE = json.load(f)
        return _CACHE

    # also try {cwd}/data/tag_categories.json
    cwd_cand = Path.cwd() / "data" / "tag_categories.json"
    if cwd_cand.exists():
        with cwd_cand.open("rb") as f:
            _CACHE = json.load(f)
        return _CACHE

    # 3. fallback empty
    _CACHE = {}
    return _CACHE