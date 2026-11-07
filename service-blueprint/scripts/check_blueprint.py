#!/usr/bin/env python3
# service-blueprint skill. Copyright 2026 Daniel Santos (danieltsantos.com). CC BY-NC 4.0, see LICENSE.txt.
"""Check a service blueprint frame + card table.

Usage:
  python check_blueprint.py <frame.yaml> <cards.csv> [--json]

Format errors (broken references, unknown values) exit with status 1.
Quality checks (SKILL.md section 12) are reported pass/fail and do not change the exit status,
because a draft can be valid data and still have open quality issues.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bp  # noqa: E402


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    frame = bp.load_frame(args[0])
    cards, missing = bp.load_cards(args[1])
    errors, quality = bp.check(frame, cards, missing)
    decisions = bp.decision_list(cards)

    if "--json" in argv:
        print(json.dumps({
            "cards": len(cards),
            "format_errors": errors,
            "quality": quality,
            "needs_decision": [{"kind": k, "id": c["id"], "title": c["title"]} for k, c in decisions],
        }, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    print(f"{len(cards)} cards, {len(frame['phases'])} phases, {len(bp.lane_list(frame)[0])} lanes")
    if errors:
        print(f"\nFORMAT ERRORS ({len(errors)}): fix these first")
        for e in errors:
            print(f"  - {e}")
    passed = sum(q["passed"] for q in quality)
    print(f"\nQUALITY CHECKS: {passed}/{len(quality)} pass")
    for q in quality:
        mark = "PASS" if q["passed"] else "FAIL"
        print(f"  [{mark}] {q['id']} {q['name']}")
        for d in q["details"][:12]:
            print(f"         - {d}")
        if len(q["details"]) > 12:
            print(f"         - ... {len(q['details']) - 12} more")
    if decisions:
        print(f"\nNEEDS A DECISION ({len(decisions)})")
        for kind, c in decisions:
            print(f"  - {kind}: {c['id']} {c['title']}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
