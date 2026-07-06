"""Standalone CLI: dump current tag-conflict rules as JSON for audit, or
validate an override file before merging into the rule table.

Usage:
    python scripts/inspect_tag_conflicts.py            # print built-ins + overrides
    python scripts/inspect_tag_conflicts.py --builtin  # built-ins only
    python scripts/inspect_tag_conflicts.py --validate path/to/overrides.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import argparse

from booru_pictag_get_mcp.core.tag_conflicts import export_rules, rule_count, load_overrides


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--builtin", action="store_true",
                    help="Ignore any override file; show only built-in rules.")
    ap.add_argument("--validate", metavar="PATH",
                    help="Validate an override JSON file shape without merging.")
    args = ap.parse_args()

    if args.validate:
        p = Path(args.validate)
        if not p.exists():
            print(f"file not found: {p}")
            return 2
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"invalid JSON: {e}")
            return 2
        if not isinstance(data, dict):
            print("top-level must be an object")
            return 2
        bad = []
        for trigger, spec in data.items():
            if not isinstance(spec, dict):
                bad.append((trigger, "spec must be object"))
                continue
            if not isinstance(spec.get("blocks", []), list):
                bad.append((trigger, "blocks must be array"))
            if not isinstance(spec.get("exceptions", {}), dict):
                bad.append((trigger, "exceptions must be object"))
        if bad:
            print("invalid entries:")
            for t, why in bad:
                print(f"  {t}: {why}")
            return 1
        print(f"OK — {len(data)} override rules, schema valid")
        return 0

    overrides = {} if args.builtin else load_overrides()
    # export_rules already reflects overrides applied at import time; that's
    # the live rule set the resolver uses.
    rules = export_rules()
    print(json.dumps({
        "rule_count": rule_count(),
        "override_triggers_loaded": list(overrides.keys()),
        "rules": rules,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())