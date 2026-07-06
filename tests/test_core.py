"""Standalone smoke test for the prompt pipeline (no network)."""

import sys
from pathlib import Path

# allow running without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from booru_pictag_get_mcp.core.clean_prompt import clean_prompt, CleanPromptOptions
from booru_pictag_get_mcp.core.background import BackgroundMode
from booru_pictag_get_mcp.core.tag_conflicts import resolve_conflicts


def test_basic_clean():
    tag_string = "1girl long_hair blue_eyes school_uniform looking_at_viewer smile simple_bg teacher_(blue_archive) signature highres"
    out = clean_prompt(
        tag_string,
        artist_tags="some_artist",
        character_tags="hatsune_miku",
        copyright_tags="vocaloid",
        # Conflict resolution is OFF by default (mirroring original cleanPrompt).
        # Multi-subject prompts must not be mangled by single-subject rules.
    )
    print("PROMPT:", out["prompt"])
    print("CATS:", out["categories"])
    print("RAW COUNT:", out["raw_tag_count"])
    assert "1girl" in out["prompt"]
    assert "highres" not in out["prompt"]
    assert "signature" not in out["prompt"]
    assert "hatsune miku" in out["prompt"]


def test_combine_redunancy():
    ts = "1girl long_hair white_hair"
    out = clean_prompt(ts)
    assert "long white hair" in out["prompt"] or "long hair" in out["prompt"]


def test_tag_conflict_resolution_explicit_opt_in():
    """Calling resolve_conflicts() directly (opt-in) DOES apply single-subject
    rules. This exists for callers who know they have a one-character prompt."""
    from booru_pictag_get_mcp.core.tag_conflicts import resolve_conflicts
    tags = ["1girl", "1boy", "smile", "crying"]
    resolved = resolve_conflicts(tags)
    # 1girl present should drop 1boy (via 1girl rule block), smile should drop crying
    assert "1boy" not in resolved
    assert "crying" not in resolved


def test_unknown_tags_pass_through():
    """Tags not in the rule set must pass through unchanged (no KeyError)."""
    from booru_pictag_get_mcp.core.tag_conflicts import resolve_conflicts, TAG_CONFLICTS
    weird = ["some_totally_unknown_tag_xyz", "another_madeup_tag_42", "1girl"]
    resolved = resolve_conflicts(weird)
    assert "some_totally_unknown_tag_xyz" in resolved
    assert "another_madeup_tag_42" in resolved
    assert "1girl" in resolved
    # 1girl block list shouldn't contain weird unknown tags either way
    rule = TAG_CONFLICTS.get("1girl")
    assert rule and "some_totally_unknown_tag_xyz" not in rule.blocks


def test_multi_subjects_not_dropped_by_default():
    """The clean_prompt default MUST NOT drop legitimate multi-character combos.

    Sex scenes need 1girl+1boy; bittersweet needs smile+crying; two characters
    can have contrasting hair lengths. Conflict rules were authored for the
    single-subject case, so the default pipeline leaves them alone.
    """
    ts = "1girl 1boy smile crying long_hair short_hair"
    out = clean_prompt(ts)
    p = out["prompt"]
    assert "1girl" in p and "1boy" in p
    assert "smile" in p and "crying" in p
    assert "long hair" in p and "short hair" in p


def test_override_merge_is_additive(tmp_path, monkeypatch):
    """External override file should add a brand-new trigger rule."""
    from booru_pictag_get_mcp.core import tag_conflicts as tc
    # Pick a trigger we can be sure isn't in the built-in set
    over = {"hatsune miku": {"blocks": ["kagamine rin"], "exceptions": {"duet": ["kagamine rin"]}}}
    f = tmp_path / "over.json"
    f.write_text(__import__("json").dumps(over), encoding="utf-8")
    monkeypatch.setenv("BOORU_TAG_CONFLICTS_OVERRIDES", str(f))
    # Reset module state then re-apply
    import importlib
    importlib.reload(tc)
    rule = tc.TAG_CONFLICTS.get("hatsune miku")
    assert rule is not None, "override should have added a new trigger"
    assert "kagamine rin" in rule.blocks
    assert "duet" in rule.exceptions and "kagamine rin" in rule.exceptions["duet"]
    # And the resolver should use it
    resolved = tc.resolve_conflicts(["hatsune miku", "kagamine rin"])
    assert "kagamine rin" not in resolved
    # But the exception wires correctly: with the duet context present, the block is exempted
    resolved2 = tc.resolve_conflicts(["hatsune miku", "kagamine rin", "duet"])
    assert "kagamine rin" in resolved2


def test_background_remove():
    ts = "1girl white_background"
    out = clean_prompt(ts, options=CleanPromptOptions(background_mode=BackgroundMode.REMOVE))
    assert "white background" not in out["prompt"]


def test_background_replace():
    ts = "1girl blue_background"
    out = clean_prompt(
        ts,
        options=CleanPromptOptions(
            background_mode=BackgroundMode.REPLACE,
            simple_background_replacement_tags="indoors, classroom",
        ),
    )
    assert "indoors" in out["prompt"]
    assert "classroom" in out["prompt"]


if __name__ == "__main__":
    test_basic_clean()
    test_combine_redunancy()
    test_tag_conflict_resolution_explicit_opt_in()
    test_unknown_tags_pass_through()
    test_multi_subjects_not_dropped_by_default()
    test_background_remove()
    test_background_replace()
    print("ALL CORE SMOKE TESTS PASSED ✅")