# AGENTS.md — instructions and memory for AI agents working on Frontend Dragon

This file is the entry point. Read it first in every session. It tells you which kind of
session you are in, which files to read (and which *not* to), what to produce, and what to
update before you stop. It also carries the project's memory: decisions already made, so
they are not re-litigated.

## The two session types

### A. Content session — writing or revising a chapter

Read, in this order, and nothing else unless a step below says so:

1. `book/context/BOOK-BRIEF.md` — what the book is (≈1,200 words)
2. `book/context/STYLE-BIBLE.md` — how it sounds and is structured (≈1,300 words)
3. `book/context/TONE-SAMPLE.md` — calibration excerpts (≈700 words)
4. `book/context/CHAPTER-SPECS.md` — the entry for the chapter you are writing, plus
   any extra spec the person gives you
5. `book/context/ATLAS-STATE.md` — where Atlas is now (≈700 words)
6. `book/context/CONTINUITY.md` — promises owed to this chapter, models to reuse,
   topics deferred (≈900 words)
7. `book/context/QC-CHECKLIST.md`

Do **not** read earlier chapters in full. If the new chapter builds directly on a specific
section of an earlier one (the continuity ledger will say so), read *that section* of
`book/manuscript/NN-*.md` only. Ask the person if in doubt.

Then:

- Write `book/manuscript/NN-slug.md` following the header convention in
  `production/DESIGN-GUIDELINES.md` §2 (three HTML comments, body starts at `##`).
- Write in parts if the chapter is long; assemble at the end. Prose, not bullets.
- Run the mechanical checks in `QC-CHECKLIST.md` (banned-phrase grep, `make lint`, counts).
- Do the editorial pass honestly. Rewrite what fails.
- **Bookkeeping, mandatory:** update `ATLAS-STATE.md`, append to `CONTINUITY.md`, flip
  the status in `CHAPTER-SPECS.md`. A chapter without these updates is not finished.
- Deliver the Markdown for review *before* building the PDF/site. The person reviews
  content first, then asks for builds.
- Do not touch `production/`.

### B. Design / pipeline session — changing how the book looks or builds

Read:

1. `production/DESIGN-GUIDELINES.md` — the whole design, both targets, and the
   manuscript conventions the build depends on
2. `production/fd/convert.py` (shared), then `fd/pdf.py` or `fd/site.py` as relevant
3. `production/book.css` or `production/site.css` as relevant

Then:

- Build against the fixture: `make fixture-pdf`, `make fixture-site`. Look at the result
  (contact sheets for print; screenshots at desktop and phone width, light and dark, for
  the site). Iterate there.
- Only when the fixture is right, run `make pdf && make site` once and inspect contact
  sheets / screenshots for the real manuscript. Do not read the manuscript's text.
- If you add a manuscript convention (a new device, a new marker), add it to all three
  places: `fd/convert.py`, `DESIGN-GUIDELINES.md` §2, and `production/fixture/01-fixture.md`.
- Do not touch `book/` except to fix a convention violation the lint reports, and say so.

### If you are unsure which session you are in

Ask. Mixing them costs a great deal of context and produces inconsistent results.

## Repository map

See `README.md`. Short version: `book/` is content, `production/` is pipeline,
`out/` is disposable.

## Decisions already made (do not reopen without the person's say-so)

- **One Markdown source, two targets** (PDF via WeasyPrint, static site). The manuscript
  never contains target-specific markup beyond the conventions in DESIGN-GUIDELINES §2.
- **Interactive web features are a layer on the prose, never a requirement.** Every
  chapter must read completely with them removed. The PDF stays viable.
- **No bookmarks, notes, progress, sync, accounts, comments, or search for now.**
- **Content and pipeline are separated** into different sessions with different reading
  lists, because a chapter is ~25k words and must not be loaded to fix a CSS bug.
- **Chapters are written one per session** from the context docs, not from prior prose.
- **Cover art** is `production/assets/cover.jpg` (Aditya's, 2:3). PDF page 1 full-bleed (typographic page follows as half-title); site index hero and sidebar thumbnail. Do not redesign it.
- **Design:** 7 × 10 in trim; Source Serif 4 / Source Sans 3 / JetBrains Mono; one
  oxblood accent `#8a3b2e`; no gradients, no card UI, no icons; the assumption callout is
  the only tinted box in body text. Web mirrors this with light/dark tokens.
- **Code ≤ 80 columns, diagrams ≤ 86 columns, diagrams ≤ ~35 lines.** Enforced by `make lint`.
- **Illustrative numbers** in Atlas (timings, sizes) are internally consistent with the
  dependency structure and may be labelled illustrative; never presented as measured
  field data.
- **Atlas decision numbering continues across chapters.** Next free number is in
  `ATLAS-STATE.md`.

## Planned work (in order)

1. Web interactive layer, step 1: experiment boxes with a "write your prediction" field
   that hides the answer until the reader commits. Convention to add: a marker in the
   manuscript that degrades to nothing in print (proposed: `<!-- lab: ch1-exp-1 -->`).
2. Hosted lab pages for Chapter 1's six experiments (static; no Node required).
3. Two or three interactive SVG diagrams (script timeline; HTTP/1.1 vs HTTP/2 waterfall).
4. Atlas v1 on the site, growing with the chapters.
5. Chapter 2 (content session) — opening question: *How wide is a `<div>`?*
6. Font subsetting / WOFF2 for the site (currently ships full OTF/TTF, ~2 MB).

## Memory log

Append dated entries. Keep each to a few lines. This is the project's memory across
machines and sessions.

- **2026-09-29** — Front matter and Chapter 1 written (~24k words) in a single session
  from the full brief. Reviewed and approved by Aditya. PDF pipeline built (WeasyPrint),
  74 pages. First contact-sheet review found: wide diagrams overflowing the measure (fixed
  by redrawing ≤ 86 cols), page-counter reset needing a named page, duplicate heading ids
  across parts breaking the TOC (fixed with per-part id prefixes).
- **2026-09-30** — Decided to add a web target and keep the PDF; interactive features are a
  layer only. Decided to split content and pipeline sessions and to write chapters from
  context docs instead of prior prose. Repo restructured into `book/` + `production/`;
  shared converter extracted; static site target built (per-chapter pages, sidebar,
  on-this-page, light/dark, mobile); fixture manuscript added; context docs written
  (brief, chapter specs, style bible, tone sample, Atlas state, continuity ledger, QC
  checklist).
- **2026-09-30 (later)** — First site review by Aditya: theme toggle was hidden on desktop (fixed: button in sidebar footer + mobile top bar); body/heading contrast too flat, especially dark (fixed: separate `--body` vs `--ink` tokens, h2 700 weight with a 2.5rem accent rule above, h3 700); anchor jumps showed the previous section (scroll-margin 4.5rem → 1.5rem desktop, 4rem mobile); cover art added to PDF and site.
- **2026-09-30 (shell pass)** — Second review: sidebar became a Notion-style hover drawer with a pin (pushes content when pinned); outline fades when idle; mobile top bar hides on scroll-down; mobile brand weight 500; theme toggle moved to a fixed top-right control; homepage simplified to centred cover + tagline + contents on all widths. Gotcha recorded: the shell script runs in `<head>`, so `document.body` must be resolved inside DOMContentLoaded. Next: web interactive layer step 1, then Chapter 2.
