"""Tag normalization utilities — ported from lib/cleanPrompt.ts (Mexes-GM, MIT)."""

from __future__ import annotations

import re


def to_space(s: str) -> str:
    return s.replace("_", " ")


def to_underscore(s: str) -> str:
    return re.sub(r"\s+", "_", s)


# Auto-corrections for common typos
COMMON_TYPOS = {
    "1 girl": "1girl",
    "2 girls": "2girls",
    "3 girls": "3girls",
    "4 girls": "4girls",
    "5 girls": "5girls",
    "6 girls": "6girls",
    "1 boy": "1boy",
    "2 boys": "2boys",
    "3 boys": "3boys",
    "4 boys": "4boys",
    "5 boys": "5boys",
    "6 boys": "6boys",
}


_BRACKET_RE = re.compile(r"^([\[\(\{<]*\s*)(.*?)(\s*(?::\s*[\d.]+)?\s*[\]\)\}>]*)$")


def normalize(s: str) -> str:
    """Lowercase, underscores→spaces, collapse whitespace, fix common typos."""
    s = to_space(s).lower().strip()
    s = re.sub(r"\s{2,}", " ", s)
    m = _BRACKET_RE.match(s)
    if m:
        prefix, core, suffix = m.group(1), m.group(2), m.group(3)
        if core in COMMON_TYPOS:
            return f"{prefix}{COMMON_TYPOS[core]}{suffix}"
    return COMMON_TYPOS.get(s, s)


def escape_parentheses(s: str) -> str:
    return s.replace("(", "\\(").replace(")", "\\)")


def parse_tag_list(input_str: str) -> list[str]:
    """Parse a tag list from a string.

    Comma-separated → split on comma (already-cleaned prompt / aiPrompt / CSV safe).
    Else if contains underscores → booru raw tag_string, split on whitespace.
    Else if contains spaces → a single multiword tag, keep as one.
    Else → single tag.
    """
    if not input_str:
        return []
    trimmed = input_str.strip()
    if not trimmed:
        return []

    if "," in trimmed:
        return [t.strip() for t in trimmed.split(",") if t.strip()]

    if "_" in trimmed:
        return [t.strip() for t in re.split(r"\s+", trimmed) if t.strip()]

    if " " in trimmed:
        return [trimmed]

    return [trimmed]


def with_normalized_variants(items: list[str]) -> set[str]:
    out: set[str] = set()
    for raw in items:
        sp = normalize(raw)
        und = to_underscore(sp)
        out.add(sp)
        out.add(und)
    return out