"""Tag classifier — ported from lib/tag-classifier.ts (Mexes-GM, MIT).

Categorizes content tags into appearance / clothing / pose / scenery / other.
"""

from __future__ import annotations

import re

CLOTHING_SUFFIXES = [
    "wear", "uniform", "costume", "dress", "bikini", "swimsuit", "lingerie",
    "underwear", "panties", "bra", "shirt", "pants", "shorts", "skirt",
    "jacket", "coat", "sweater", "hoodie", "vest", "gloves", "mittens",
    "shoes", "boots", "sneakers", "socks", "stockings", "pantyhose",
    "leggings", "hat", "cap", "helmet", "glasses", "eyewear", "mask",
    "necklace", "earrings", "jewelry", "ribbon", "tie", "scarf", "belt",
    "bag", "backpack", "armor", "bodysuit", "leotard", "apron", "kimono", "yukata",
]

POSE_KEYWORDS = [
    "standing", "sitting", "lying", "kneeling", "squatting", "walking",
    "running", "jumping", "flying", "swimming", "sleeping", "looking",
    "view", "leaning", "reaching", "holding", "carrying", "hugging",
    "kissing", "arms up", "arms behind", "legs crossed", "legs apart",
    "selfie", "peace sign", "stretching", "crying", "laughing", "smiling",
    "blush", "expression", "looking at viewer", "looking back", "from behind",
    "from below", "from above", "side view", "back view"
]

SCENERY_KEYWORDS = [
    "indoors", "outdoors", "background", "sky", "cloud", "sun", "moon",
    "star", "water", "sea", "ocean", "river", "lake", "pool", "beach",
    "mountain", "forest", "tree", "flower", "grass", "plant", "nature",
    "city", "town", "village", "building", "house", "room", "bed",
    "couch", "chair", "table", "window", "door", "floor", "wall",
    "ceiling", "road", "street", "ruins", "scenery", "landscape",
    "night", "day", "sunset", "sunrise", "rain", "snow"
]

APPEARANCE_KEYWORDS = [
    "1girl", "1boy", "2girls", "2boys", "hair", "eyes", "skin",
    "breasts", "chest", "nipples", "pussy", "penis", "tail", "wings",
    "horns", "ears", "animal", "fur", "scales", "muscle", "fat",
    "pregnant", "tall", "short", "body", "face", "grin", "smile",
    "blonde", "brunette", "redhead", "silver", "grey", "blue", "green",
    "heterochromia", "ahoge", "twintails", "ponytail", "braid", "buns"
]


def _compile_keywords(keywords: list[str]) -> list[re.Pattern]:
    return [re.compile(rf"\b{re.escape(k)}\b") for k in keywords]


POSE_REGEXES = _compile_keywords(POSE_KEYWORDS)
SCENERY_REGEXES = _compile_keywords(SCENERY_KEYWORDS)
APPEARANCE_REGEXES = _compile_keywords(APPEARANCE_KEYWORDS)


def classify_tag(tag: str, overrides: dict | None = None) -> str:
    """Return one of: clothing, pose, scenery, appearance, other."""
    lower_with_spaces = tag.lower().replace("_", " ")

    # 1. Overrides
    if overrides:
        override_value = overrides.get(lower_with_spaces) or overrides.get(tag.lower())
        if not override_value and " " in lower_with_spaces:
            cleaned = (re.sub(r"[<>\[\](){}]", "", lower_with_spaces)
                       .strip())
            cleaned = re.sub(r":\s*\d+(\.\d+)?\s*$", "", cleaned)
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
            parts = cleaned.split(" ")
            current = ""
            for i in range(len(parts) - 1, -1, -1):
                current = parts[i] if not current else f"{parts[i]} {current}"
                if current == cleaned:
                    continue
                if current in overrides:
                    override_value = overrides[current]
                    break
        if override_value:
            cat = str(override_value).lower().strip()
            if cat in ("clothing", "pose", "scenery", "appearance", "other"):
                return cat

    subject = (re.sub(r"[<>\[\](){}]", "", lower_with_spaces)
               .strip())
    subject = re.sub(r":\s*\d+(\.\d+)?\s*$", "", subject)
    subject = re.sub(r"\s{2,}", " ", subject).strip()
    parts = subject.split(" ")
    last = parts[-1] if parts else ""

    if any(subject.endswith(sfx) or f" {sfx}" in subject for sfx in CLOTHING_SUFFIXES):
        return "clothing"

    if any(rx.search(subject) for rx in POSE_REGEXES):
        return "pose"

    if any(rx.search(subject) for rx in SCENERY_REGEXES) or subject.endswith(" background"):
        return "scenery"

    if any(rx.search(subject) for rx in APPEARANCE_REGEXES) or last == "hair" or last == "eyes":
        return "appearance"

    if "(" in lower_with_spaces and ")" in lower_with_spaces:
        return "appearance"

    return "other"


def classify_tags(tags: list[str], overrides: dict | None = None,
                  known_character_tags: list[str] | None = None) -> dict:
    """Return dict with categories. Character tags are pushed to appearance."""
    result = {
        "clothing": [],
        "pose": [],
        "scenery": [],
        "appearance": [],
        "other": [],
    }

    def _norm_match(s: str) -> str:
        v = s.lower().replace("_", " ")
        v = re.sub(r"\\(?=[()])", "", v).strip()
        return v

    char_set = set(_norm_match(t) for t in (known_character_tags or []))

    for tag in tags:
        if _norm_match(tag) in char_set:
            result["appearance"].append(tag)
            continue
        cat = classify_tag(tag, overrides)
        if cat in result:
            result[cat].append(tag)
        else:
            result["other"].append(tag)

    return result


def get_smart_combined_tags(tags: list[str]) -> list[str]:
    """Remove tags that are substrings of an already-kept (longer) tag."""
    unique = list(dict.fromkeys(tags))
    sorted_unique = sorted(unique, key=len, reverse=True)
    kept: list[str] = []
    for tag in sorted_unique:
        if not any(k != tag and tag in k for k in kept):
            kept.append(tag)
    return list(reversed(kept))