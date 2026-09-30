#!/usr/bin/env python3
"""
Frontend Dragon — build CLI.

    python3 production/build.py pdf                 # book/manuscript → out/Frontend-Dragon.pdf
    python3 production/build.py site                # book/manuscript → out/site/
    python3 production/build.py lint                # width checks on fenced blocks
    python3 production/build.py pdf --fixture       # build from production/fixture instead (design sessions)
    python3 production/build.py site --fixture
    python3 production/build.py pdf --html-only     # paged HTML only, no WeasyPrint

Manuscript conventions: production/DESIGN-GUIDELINES.md
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from fd.convert import load_manuscript, lint_manuscript  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Build Frontend Dragon")
    ap.add_argument("target", choices=["pdf", "site", "lint", "all"])
    ap.add_argument("--fixture", action="store_true", help="use production/fixture as the manuscript")
    ap.add_argument("--manuscript", help="explicit manuscript directory")
    ap.add_argument("--out", default=os.path.join(REPO, "out"))
    ap.add_argument("--html-only", action="store_true")
    args = ap.parse_args()

    ms = args.manuscript or (os.path.join(HERE, "fixture") if args.fixture else os.path.join(REPO, "book", "manuscript"))
    name = "Fixture" if args.fixture else "Frontend-Dragon"

    problems = lint_manuscript(ms)
    for p in problems:
        print("lint:", p)
    if args.target == "lint":
        sys.exit(1 if problems else 0)

    parts, chapters = load_manuscript(ms)
    if args.target in ("pdf", "all"):
        from fd.pdf import build_pdf
        build_pdf(parts, chapters, HERE, args.out, name=name, html_only=args.html_only)
    if args.target in ("site", "all"):
        from fd.site import build_site
        build_site(parts, chapters, HERE, args.out)


if __name__ == "__main__":
    main()
