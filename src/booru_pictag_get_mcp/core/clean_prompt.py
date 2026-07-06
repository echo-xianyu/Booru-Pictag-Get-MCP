"""Prompt cleaner — ported from lib/cleanPrompt.ts (Mexes-GM, MIT).

Public API: clean_prompt(...) -> {prompt, categories, raw_tag_count}.
"""

from __future__ import annotations

import re
from typing import Optional

from .normalize import (
    normalize, to_space, to_underscore, parse_tag_list,
    escape_parentheses, with_normalized_variants,
)
from .tag_classifier import classify_tags
from .background import process_background_tags, BackgroundMode


# --------------- Domain Sets ---------------

BREAST_SIZES_SET = {normalize(x) for x in [
    "flat chest", "small breasts", "medium breasts", "large breasts",
    "huge breasts", "gigantic breasts",
]}

HAIR_LENGTHS_SET = {normalize(x) for x in [
    "bald", "very short hair", "short hair", "medium hair", "long hair",
    "very long hair", "absurdly long hair",
]}

EYE_COLORS_SET = {normalize(x) for x in [
    "blue eyes","brown eyes","green eyes","red eyes","purple eyes","yellow eyes",
    "pink eyes","orange eyes","black eyes","white eyes","gray eyes","grey eyes",
]}

QUALITY_TAGS_SET = {normalize(x) for x in [
    "masterpiece","best quality","high quality","ultra-detailed","detailed",
    "extremely detailed","highly detailed","amazing quality","newest",
    "beautiful lighting","soft reflections","amazing composition","flat color",
]}

SUBJECT_TAGS_SET = {normalize(x) for x in [
    "1girl","1boy","2girls","2boys","multiple girls","multiple boys",
]}

COMPOSITION_TAGS_SET = {normalize(x) for x in [
    "portrait","full body","upper body","close-up","wide shot",
]}


# --------------- Curated meta tags to remove ---------------

FALLBACK_META_TAGS = [
    "signature", "twitter username", "artist name", "watermark", "copyright",
    "artist", "unknown artist", "official art", "fan art", "commission",
    "pointless censoring", "web address", "original", "sound effects",
    "motion lines", "patreon logo", "copyright notice", "commissioner name",
    "borrowed character", "borrowed character name", "bad id", "bad pixiv id",
    "request", "commentary", "translated", "highres", "absurdres",
]

CURATED_META_LIST_RAW = [
    # resolution/commentary
    "highres","absurdres","commentary","commentary request","english commentary",
    "chinese commentary","korean commentary","mixed-language commentary","partial commentary",
    "translated","translation request",
    "one-hour drawing challenge","one hour drawing challenge",
    # web/url/logo/ids
    "web address","+web address+","patreon logo","copyright notice","official art","commission",
    "bad id","bad pixiv id","bad artstation id","bad facebook id","bad instagram id","bad tiktok id",
    "bad reddit id","bad github id","bad discord id","bad telegram id","bad skype id","bad other id","bad twitter id",
    "photoshop (medium)","symbol-only commentary","artist request","copyright request","non-web source",
    "signature","watermark","artist name","twitter username","request",
    "english text","japanese text","chinese text","korean text","text","speech bubble","dialogue",
    "subtitle","caption","logo","brand logo","company logo","game logo","anime logo","manga logo",
    "instagram logo","pixiv logo","twitter logo","ko fi logo","ko-fi logo",
    "character name","series name","franchise name","copyright name","trademark",
    "patreon username","pixiv username","deviantart username","artstation username","instagram username",
    "facebook username","bluesky username","tumblr username","discord username","username","handle",
    "inactive account","deleted account","banned account","virtual youtuber","vtuber","streamer","content creator",
    "weibo watermark","tiktok watermark","instagram watermark","facebook watermark",
    "social media watermark","website watermark","url","link","qr code","barcode","metadata","file info",
    "image info","photo info","camera info","timestamp","date","time",
    "artist logo","pixiv request","twitter request","source request","character request",
    "pool request","post request","source edit","artist edit","character edit","copyright edit",
    "banned artist","duplicate","replaced","repost","inaccurate tag","poorly drawn","bad anatomy",
    "bad hands","bad proportions","bad perspective","bad source","missing tag","partially translated",
    "check translation","tagme","tag request","tag update","needs tags","needs source","needs id",
    "needs commentary","needs translation","unneeded tag","wrong tag","deletion request","hard translated",
    "partially hard translated","third-party edit","revision","sample","resized","upscaled","downscaled",
    "lossy-lossless","jpeg artifacts","compression artifacts","alternate source","secondary source",
    "copyright text","watermark text","logo text","brand name","company name","studio name",
    "production name","fanbox username","gumroad username","ko fi username","ko-fi username",
    "subscribestar username","fanbox watermark","gumroad watermark","ko fi watermark",
    "subscribestar watermark","transparent background","white background only","solid color background",
    "single color background","minimalist background","empty space","negative space","simple color background",
    # censorship variants
    "censored","censorship","bar","mosaic","blur","pixelated","censor","uncensored","decensor",
    "uncensored version","censored version","black bar","white bar","mosaic censorship","pixel censorship",
    "light censorship","heavy censorship","partial censorship","full censorship","genital censor",
    "nipple censor","penis censor","vagina censor","pussy censor","ass censor","butt censor",
    "breast censor","nipple bar","genital bar","penis bar","vagina bar","pussy bar","ass bar",
    "butt bar","breast bar","nipple blur","genital blur","penis blur","vagina blur","pussy blur",
    "ass blur","butt blur","breast blur","nipple mosaic","genital mosaic","penis mosaic",
    "vagina mosaic","pussy mosaic","ass mosaic","butt mosaic","breast mosaic","bar censor",
    "mosaic censor","blur censor","mosaic censoring","censoring","dated","original",
    # Additional meta tags from Danbooru
    "lowres","variant set","game asset","partial commentary","untranslatable commentary",
    "paid reward available","traditional media","md5 mismatch","skeb commission","large variant set",
    "third-party source","animated","incredible absurdres","nominated","unlisted","screencap","video",
    "webm","image","flash","uncompressed file","colorized","pre-rendered 3d",
]

META_TAGS_SET: set[str] = set()
META_TAGS_SET.update(normalize(x) for x in FALLBACK_META_TAGS)
META_TAGS_SET.update(with_normalized_variants(CURATED_META_LIST_RAW))


# --------------- Optimization helpers ---------------

_NUM_RE = re.compile(r"^\d+$")
_URL_RE = re.compile(r":")
_BRACKET_RE = re.compile(r"[(){}\[\]]")
_SPACE_RE = re.compile(r"\s{2,}")


_ACTION_VERB_ADJECTIVES = {normalize(x) for x in [
    "grabbing","holding","pulling","lifting","adjusting","removing","gripping","clutching",
    "tugging","untying","unbuttoning","unzipping","unfastening","hiking","raising","fixing",
    "touching","hugging","wearing","showing","covering","opening","closing","wringing",
]}

_EXCLUSIVE_ADJ_FAMILIES = [
    ["long","short","medium","micro","mini","maxi"],
    ["torn","intact"],
    ["open","closed","unbuttoned","buttoned"],
    ["wet","dry"],
    ["sleeveless","long-sleeved","short-sleeved"],
]
_ADJ_FAMILY_MAP: dict[str, int] = {}
for fam_id, fam in enumerate(_EXCLUSIVE_ADJ_FAMILIES):
    for adj in fam:
        _ADJ_FAMILY_MAP[normalize(adj)] = fam_id


_MERGE_NOUNS = {normalize(x) for x in [
    "skirt","dress","shirt","jacket","coat","cape","hat","hood","boots","socks",
    "stockings","gloves","pants","shorts","leggings","tights","apron","kimono",
    "yukata","armor","bikini","swimsuit","underwear","panties","bra","hair",
]}


def _combine_shared_noun_tags(original: list[str]) -> list[str]:
    groups: dict[str, dict] = {}
    for idx, tag in enumerate(original):
        parts = tag.split(" ")
        if len(parts) != 2:
            continue
        adj, noun = parts
        if noun not in _MERGE_NOUNS:
            continue
        if adj in _ACTION_VERB_ADJECTIVES:
            continue
        g = groups.setdefault(noun, {"indices": [], "adjectives": []})
        g["indices"].append(idx)
        if adj not in g["adjectives"]:
            g["adjectives"].append(adj)

    to_skip: set[int] = set()
    insertion_map: dict[int, str] = {}

    for noun, info in groups.items():
        if len(info["indices"]) <= 1:
            continue
        seen_families: set[int] = set()
        has_conflict = False
        for adj in info["adjectives"]:
            fam_id = _ADJ_FAMILY_MAP.get(normalize(adj))
            if fam_id is None:
                continue
            if fam_id in seen_families:
                has_conflict = True
                break
            seen_families.add(fam_id)
        if has_conflict:
            continue
        combined = " ".join(info["adjectives"] + [noun]).strip()
        if combined in original:
            for i in info["indices"]:
                to_skip.add(i)
            combined_index = original.index(combined)
            to_skip.discard(combined_index)
        else:
            insertion_map[info["indices"][0]] = combined
            for i in info["indices"]:
                to_skip.add(i)

    if not insertion_map:
        return original

    result: list[str] = []
    for idx, tag in enumerate(original):
        if idx in insertion_map:
            result.append(insertion_map[idx])
        elif idx in to_skip:
            pass
        else:
            result.append(tag)
    return result


def _remove_redundant_by_inclusion(tag_list: list[str]) -> list[str]:
    items = []
    for t in tag_list:
        words = [w for w in t.split(" ") if w.strip()]
        items.append((t, words, set(words)))
    items.sort(key=lambda x: len(x[0]), reverse=True)

    kept_set: set[str] = set()
    kept_list: list = []
    for tag, words, words_set in items:
        if tag in kept_set:
            continue
        is_covered = False
        for pt, pw, pws in kept_list:
            if pt.find(tag) == -1:
                continue
            if all(w in pws for w in words):
                is_covered = True
                break
        if not is_covered:
            kept_set.add(tag)
            kept_list.append((tag, words, words_set))
    return [t for t in tag_list if t in kept_set]


def _breast_hierarchy(t: str) -> int | None:
    h = ["gigantic breasts","huge breasts","large breasts","medium breasts","small breasts","flat chest"]
    return h.index(t) if t in h else None


def _hair_length_hierarchy(t: str) -> int | None:
    h = ["absurdly long hair","very long hair","long hair","medium hair","short hair","very short hair","bald"]
    return h.index(t) if t in h else None


def _optimize_tags(tags: list[str]) -> list[str]:
    working = list(tags)
    subject_tags_norm = [normalize(t) for t in working]
    subject_set = set(subject_tags_norm)
    has_plural = any(x in subject_set for x in (
        "2girls","2boys","3girls","3boys","4girls","4boys","5girls","5boys",
        "6+girls","6+boys","multiple girls","multiple boys",
        "couple","group","duo","trio","threesome","group sex","twins","siblings",
    ))
    has_distinct_subject_count = sum(1 for t in subject_set if t in SUBJECT_TAGS_SET or t in (
        "2girls","2boys","3girls","3boys","4girls","4boys","multiple girls","multiple boys",
        "couple","group","duo","trio","twins","siblings",
    )) > 1
    disable_combo = has_plural or has_distinct_subject_count

    # Multi-character frames don't have a single "most specific" hair length or
    # eye color — different characters may legitimately have different ones.
    # Skip the "keep best per hierarchy" dedup in that case; tag_conflicts and
    # the combine step downstream already protect against truly contradictory
    # single-character tag pairs.
    skip_hierarchy_dedup = has_plural or has_distinct_subject_count

    # 1) keep most specific breast size (hierarchy order) — single-subject only
    present_breasts = [t for t in [
        normalize("gigantic breasts"), normalize("huge breasts"),
        normalize("large breasts"), normalize("medium breasts"),
        normalize("small breasts"), normalize("flat chest"),
    ] if t in working]
    if not skip_hierarchy_dedup and len(present_breasts) > 1:
        best = present_breasts[0]
        working = [t for t in working if not (t in BREAST_SIZES_SET and t != best)]

    # 2) keep most specific hair length — single-subject only
    present_hair = [t for t in [
        normalize("absurdly long hair"), normalize("very long hair"),
        normalize("long hair"), normalize("medium hair"), normalize("short hair"),
        normalize("very short hair"), normalize("bald"),
    ] if t in working]
    if not skip_hierarchy_dedup and len(present_hair) > 1:
        best = present_hair[0]
        working = [t for t in working if not (t in HAIR_LENGTHS_SET and t != best)]
    # exact-duplicate hair-length dedup (not hierarchy collapse) still applies
    seen_hair: set[str] = set()
    working = [t for t in working if not (t in HAIR_LENGTHS_SET and (t in seen_hair or seen_hair.add(t)))]

    # 3) dedupe eye color (exact duplicate only, first wins)
    seen_eyes: set[str] = set()
    new = []
    for t in working:
        if t in EYE_COLORS_SET:
            if t in seen_eyes:
                continue
            seen_eyes.add(t)
        new.append(t)
    working = new

    # 4) combine adjectives for same noun (single-subject only — two characters
    #    may each have "long hair" + "white hair" vs "short hair" + "black hair"
    #    which we must NOT collapse into a single combined tag).
    if not disable_combo:
        working = _combine_shared_noun_tags(working)

    # 5) remove redundant by inclusion
    working = _remove_redundant_by_inclusion(working)
    return working


# --------------- Main API ---------------

class CleanPromptOptions:
    def __init__(
        self,
        include_characters: bool = True,
        include_copyrights: bool = True,
        optimize: bool = True,
        exclude: Optional[list[str]] = None,
        added_tags: Optional[list[str]] = None,
        tag_overrides: Optional[dict] = None,
        escape_output: bool = True,
        meta_tags: Optional[str] = None,
        background_mode: BackgroundMode = BackgroundMode.KEEP,
        simple_background_replacement_tags: Optional[str] = None,
        resolve_conflicts: bool = False,
        detailed_backgrounds_list: Optional[list[list[str]]] = None,
        background_seed: Optional[int] = None,
        random_background_include_gradients: bool = False,
        random_background_patterns: bool = True,
    ):
        self.include_characters = include_characters
        self.include_copyrights = include_copyrights
        self.optimize = optimize
        self.exclude = exclude or []
        self.added_tags = added_tags or []
        self.tag_overrides = tag_overrides
        self.escape_output = escape_output
        self.meta_tags = meta_tags
        self.background_mode = background_mode
        self.simple_background_replacement_tags = simple_background_replacement_tags
        self.resolve_conflicts = resolve_conflicts
        self.detailed_backgrounds_list = detailed_backgrounds_list
        self.background_seed = background_seed
        self.random_background_include_gradients = random_background_include_gradients
        self.random_background_patterns = random_background_patterns


def clean_prompt(
    tag_string: str,
    artist_tags: str = "",
    character_tags: str = "",
    copyright_tags: str = "",
    options: CleanPromptOptions | None = None,
) -> dict:
    """Return {prompt, categories, raw_tag_count}."""
    if options is None:
        options = CleanPromptOptions()

    include_chars = options.include_characters
    include_copyrights = options.include_copyrights
    optimize_all = options.optimize

    user_exclude = {normalize(t) for t in options.exclude if t.strip()}

    all_tags = parse_tag_list(tag_string)
    artist_set = {normalize(t) for t in parse_tag_list(artist_tags)}
    char_arr = parse_tag_list(character_tags)
    cp_arr = parse_tag_list(copyright_tags)

    api_meta_set = {normalize(t) for t in parse_tag_list(options.meta_tags or "")}

    # Sliding-window meta removal for multiword meta sequences
    multiword_meta = {t for t in META_TAGS_SET if " " in t}
    multiword_meta.add(normalize("web address"))
    multiword_meta.add(normalize("web_address"))
    if multiword_meta and len(all_tags) > 1:
        lowered = [normalize(t) for t in all_tags]
        new_tokens: list[str] = []
        i = 0
        while i < len(lowered):
            matched = False
            for span in range(4, 1, -1):
                if i + span > len(lowered):
                    continue
                sl = lowered[i:i + span]
                cand_space = " ".join(sl)
                cand_und = to_underscore(cand_space)
                if cand_space in multiword_meta or cand_und in multiword_meta:
                    i += span
                    matched = True
                    break
            if not matched:
                new_tokens.append(all_tags[i])
                i += 1
        all_tags = new_tokens

    norm_char_set = {normalize(t) for t in char_arr if t.strip()}
    norm_cpy_set = {normalize(t) for t in cp_arr if t.strip()}

    def _is_filtered_out(raw: str) -> bool:
        if len(raw) <= 1:
            return True
        lower = raw.lower()
        if lower in artist_set or normalize(lower) in artist_set:
            return True
        if normalize(lower) in META_TAGS_SET:
            return True
        if normalize(lower) in api_meta_set:
            return True
        if _NUM_RE.match(raw):
            return True
        if "@" in raw or "#" in raw or _URL_RE.search(raw):
            return True
        if _BRACKET_RE.search(raw):
            return True
        return False

    filtered = [t for t in all_tags if not _is_filtered_out(t)]
    formatted = [normalize(t) for t in filtered if normalize(t) not in user_exclude]

    processed = _optimize_tags(formatted) if optimize_all else formatted

    # NOTE: tag-conflict resolution is intentionally NOT part of the default
    # pipeline. The original booru-prompt-gallery's cleanPrompt does not call
    # tag-conflicts.ts either; its contradiction rules were applied elsewhere
    # (UI card layer) and only on single-character posts.
    #
    # Running them inside clean_prompt by default would actively *hurt* common
    # multi-character prompts — e.g. sex scenes (1girl + 1boy), bittersweet
    # moods (smile + crying), two characters with different hairstyles
    # (long_hair + short_hair) — because the rules were authored assuming a
    # single subject. Callers who still want the (single-subject) resolver can
    # invoke booru_pictag_get_mcp.core.tag_conflicts.resolve_conflicts themselves; the
    # `CleanPromptOptions.resolve_conflicts` flag below is retained as a no-op
    # hook for forward compatibility but currently does nothing.
    if options.resolve_conflicts:
        from .tag_conflicts import resolve_conflicts
        processed = resolve_conflicts(processed)

    # Partition quality vs content
    quality_tags: list[str] = []
    content_tags: list[str] = []
    for t in processed:
        if t in QUALITY_TAGS_SET:
            quality_tags.append(t)
        else:
            content_tags.append(t)

    classified = classify_tags(content_tags, options.tag_overrides)
    sorted_content = (classified["appearance"] + classified["clothing"]
                      + classified["pose"] + classified["scenery"] + classified["other"])

    if options.background_mode != BackgroundMode.KEEP:
        sorted_content = process_background_tags(
            sorted_content,
            options.background_mode,
            options.simple_background_replacement_tags,
            options.tag_overrides,
            options.random_background_patterns,
            options.random_background_include_gradients,
            options.detailed_backgrounds_list,
            options.background_seed,
        )

    char_and_franchise = [t for t in [
        *(char_arr if include_chars else []),
        *(cp_arr if include_copyrights else []),
    ] if t.strip()]
    char_and_franchise = [normalize(t) for t in char_and_franchise if t.strip()]

    final_add = [normalize(t) for t in options.added_tags if t.strip() and normalize(t) not in user_exclude]

    all_final: list[str] = []

    # 1. added tags
    for t in final_add:
        if t not in all_final:
            all_final.append(t)

    # 2 character/copyright
    for t in char_and_franchise:
        if t in user_exclude:
            continue
        if t not in all_final:
            all_final.append(t)

    # 3 content + quality at the end
    combined_pre = sorted_content + quality_tags
    added_set = set(final_add)
    for t in combined_pre:
        if not include_chars and t in norm_char_set:
            continue
        if not include_copyrights and t in norm_cpy_set:
            continue
        if not include_chars and (t.startswith("official ") or t.startswith("alternate ")):
            continue
        if t in user_exclude:
            continue
        if t not in all_final:
            all_final.append(t)

    should_escape = options.escape_output
    out_tags = []
    for t in all_final:
        if should_escape and t not in added_set:
            out_tags.append(escape_parentheses(t))
        else:
            out_tags.append(t)

    raw_tag_count = len(parse_tag_list(tag_string))

    return {
        "prompt": ", ".join(out_tags),
        "categories": {
            "appearance": classified["appearance"],
            "clothing": classified["clothing"],
            "pose": classified["pose"],
            "scenery": classified["scenery"],
            "character": char_and_franchise,
            "quality": quality_tags,
            "other": classified["other"],
        },
        "raw_tag_count": raw_tag_count,
    }