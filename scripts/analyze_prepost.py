#!/usr/bin/env python3
"""
Interactive pre-post analysis CLI for @a.storyof.two.
Runs the full 5-agent pre-post pipeline on a planned Reel.

Usage:
    python scripts/analyze_prepost.py
    python scripts/analyze_prepost.py --concept "Anchal threatens to leave the house again"
    python scripts/analyze_prepost.py --concept "..." --caption "..." --audio "..."
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.b1_prepost import analyze_prepost, interactive_mode
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pre-post Reel analysis — @a.storyof.two",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_prepost.py
  python scripts/analyze_prepost.py --concept "Anchal tries Kashmiri wazwan for the first time"
  python scripts/analyze_prepost.py --concept "..." --hook "Opens on Anchal holding a suitcase" --caption "me threatening to leave (again)"
        """,
    )
    parser.add_argument("--concept", help="Video concept (one sentence)")
    parser.add_argument("--hook", dest="hook_plan", help="Hook plan — what happens in the first 3 seconds")
    parser.add_argument("--caption", dest="caption_draft", help="Caption draft")
    parser.add_argument("--edit", dest="edit_plan", help="Edit plan or scene structure")
    parser.add_argument("--audio", help="Planned audio track or category")
    parser.add_argument("--cover", dest="cover_frame", help="Cover frame description")
    parser.add_argument("--no-save", action="store_true", help="Print only; don't save to output/prepost/")

    args = parser.parse_args()

    if args.concept:
        brief = {
            "concept": args.concept,
            "hook_plan": args.hook_plan,
            "caption_draft": args.caption_draft,
            "edit_plan": args.edit_plan,
            "audio": args.audio,
            "cover_frame": args.cover_frame,
        }
        brief = {k: v for k, v in brief.items() if v}
    else:
        brief = interactive_mode()

    report = analyze_prepost(brief, save=not args.no_save)

    print("\n" + "=" * 60 + "\n")
    print(report)
