# Frontend Dragon — Design & Production Guidelines

The single reference for typesetting the book, in print and on the web. A design or
pipeline session should be able to read *only this file* (plus the code it points at),
build against the fixture, and ship a change without opening a real chapter. A content
session needs only §2.

| File | Purpose |
|---|---|
| `production/build.py` | CLI: `pdf`, `site`, `lint`, `all`; `--fixture` swaps in `production/fixture/` |
| `production/fd/convert.py` | Markdown → HTML, all manuscript conventions interpreted here, lint |
| `production/fd/pdf.py` | Print target: cover, colophon, TOC, chapter openers → WeasyPrint |
| `production/fd/site.py` | Web target: index, one page per part/chapter, sidebar, on-this-page, pager |
| `production/book.css` | Print design (paged-media CSS) |
| `production/site.css` | Web design (same tokens; light/dark; responsive) |
| `production/fixture/` | Small manuscript exercising every device — build against this |
| `production/assets/` | `cover.jpg` (print, full-bleed page 1) and `cover-512.jpg` (site thumbnail) |
| `production/fetch-fonts.sh` | Downloads Source Serif 4, Source Sans 3, JetBrains Mono into `production/fonts/lib/` |

## 1. Building

```
make setup && make fonts        # once per machine (see README for native deps)
make pdf | make site | make all
make lint                       # width checks; run before any build
make fixture-pdf / fixture-site # design sessions build these, not the real book
make contact-sheet              # thumbnails of every PDF page into out/pg/
```

Always look at the output after a build. Print: contact sheets, then two or three pages
at ~100 dpi. Web: screenshots at 1440 px and 390 px, light and dark (a Playwright
one-liner is fine). Things that only show up visually: code wider than the measure,
figures pushed to a new page leaving a gap, headings orphaned at a page bottom, wrong TOC
numbers, a sidebar that does not collapse on a phone.

## 2. Manuscript conventions (what the build script expects)

### Chapter file header

Files live in `book/manuscript/`. Every chapter file begins with exactly these three HTML comments, then a blank line,
then the body starting at a level-2 heading:

```
<!-- chapter: 2 -->
<!-- title: Layout, Typography, and Pixels -->
<!-- question: How wide is a div? -->

## The Question
...
```

`question` becomes the italic epigraph on the opener page. Keep it one line.
Do **not** put a `# Chapter N` or `# Title` heading in the file; the build generates the
opener from the metadata. (The `#` level is reserved for front-matter parts.)

### Heading levels

* `##` — major section of a chapter. Appears in the TOC and as the recto running head.
  Aim for 12–20 per chapter. Titles should be short (≤ 45 characters) so the running head fits.
* `###` — subsection. Not in the TOC.
* `####` — rare; italic run-in style. Use only inside long subsections.
* Two sections have reserved names that the build styles specially and forces onto a new
  page: `## Exercises` and `## Further Exploration`. Use those exact strings.
* Inside Exercises, category headings are `###` in the form `### Prediction`,
  `### Explanation`, `### Debugging`, `### Experiment`, `### Design`, `### Source exploration`.
  They render as small caps.
* Inside Further Exploration, categories are `###` (`### Read next`, `### Read deeper`,
  `### Inspect real systems`, `### Optional rabbit holes`).

### Recurring devices (detected by pattern — spell them exactly)

| Device | Markdown | Rendering |
|---|---|---|
| Assumption callout | Paragraph beginning `*Assumption to notice:* we assumed …` | Tinted box, accent rule on the left, label in small caps; first letter auto-capitalized |
| Prediction prompt | Paragraph beginning `*Predict:* …` | Accent-colored label |
| Atlas decision | Paragraph beginning `*Decision 3. Short title.* Body…` | Bold sans run-in title |
| Experiment heading | `### Experiment 4: The waterfall under throttling` | Accent-colored h3 |
| Exercise | Paragraph beginning `**2.7** …` (chapter.number in bold) | Hanging-indent number in accent |
| Difficulty marks | `◆` and `◆◆` after the exercise number | Plain glyphs |
| Section break within a section | A line containing only `---` | Centered `• • •` |
| Table | Standard pipe table | Sans, thin rules, no zebra stripes |

Do not invent new labelled paragraph types without adding a rule to `postprocess()` in
`fd/convert.py`, a style in **both** `book.css` and `site.css`, and an instance in `fixture/01-fixture.md`; otherwise they render as ordinary italic.

### Code blocks vs. diagrams

* A fenced block **with** a language (`js`, `ts`, `html`, `css`, `json`, `http`, `bash`)
  is a *code block*: tinted background, syntax highlighting in a muted palette.
* A fenced block **without** a language is a *diagram/figure*: no background, thin rules
  above and below, slightly smaller monospace, muted ink. Use this for ASCII diagrams,
  timelines, waterfalls, equations, and header dumps you do not want highlighted.
* **Hard limit: 80 characters per line** for code, **≤ 86** for diagrams. Wider lines
  overflow the right margin (the measure is ~5.4 in). The build shrinks diagrams wider than
  92 columns slightly, but that is a safety net, not a target. Reflow instead.
* Code blocks longer than 18 lines are allowed to break across pages; shorter ones and all
  diagrams are kept whole (which can leave a gap at a page bottom — acceptable for figures).
* Box-drawing characters (`─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ═ ║ ╪ ╢`), arrows (`─▶ ◀── → ▼ ▲`) and
  block glyphs (`█ ▒ ▐ ▌`) all render correctly in JetBrains Mono. Prefer `─▶` over `-->`.
* Keep diagrams under ~35 lines so they fit a page with a caption paragraph.

### Prose conventions that affect layout

* Inline code with backticks is fine in running text but avoid it in headings.
* Use `*italic*` for emphasis and defined terms; `**bold**` only for exercise numbers and
  the bold lead-ins in "Breaking the Model"-style lists. Bold is deliberately rare.
* Bulleted lists are legal but styled minimally; the book's voice is paragraphs.
* Use real typographic quotes and dashes freely; `smarty` converts straight ones.
* Arrows in prose (`→`) are fine and render in the serif.

## 3. The design, and why

**Trim and measure.** 7 × 10 in page, margins 0.85 in top, 0.8 in outer/inner, 0.9 in bottom.
Text measure ≈ 5.4 in → 68–75 characters per line at 10.5 pt. This is the comfortable
range for sustained technical reading; do not widen it.

**Typefaces.** Body: *Source Serif 4* 10.5/15.2 pt, justified with hyphenation
(`lang="en"` must stay on `<html>` for hyphenation to work). Headings, tables, labels,
running heads: *Source Sans 3* semibold. Code: *JetBrains Mono* 8.3 pt in blocks,
0.86 em inline, ligatures off. All three are open-licensed and bundled via `fetch-fonts.sh`.
Fallbacks are not configured on purpose: a missing font should be noticed, not silently
substituted.

**Colour.** Ink `#1c1b19` (not pure black). One accent, oxblood `#8a3b2e`, used only for:
chapter numerals, TOC chapter numbers, experiment headings, callout labels and rules,
exercise numbers, the cover band. Nothing else is coloured. Tints: `#f6f4f0` for code,
`#f3efe6` for callouts. No gradients, no filled heading bars, no card UI.

**Hierarchy.** Chapter opener: small-caps "CHAPTER", a 96 pt accent numeral, 27 pt sans
title, italic epigraph with a thin accent rule. Openers always start on a recto (right)
page; the preceding blank verso carries no running head or folio. `##` at 15 pt sans,
`###` at 11.5 pt, `####` italic run-in. Headings never sit alone at a page bottom
(`break-after: avoid`).

**Running heads and folios.** Verso (left) top-left: `CHAPTER N · TITLE` in small caps.
Recto (right) top-right: current `##` section title in italic. Page number centred at the
bottom in the serif. Front matter uses lowercase roman folios; Arabic numbering restarts at
1 on the Chapter 1 opener (done with a named page `opener-first` — do not move that rule).

**Front matter.** Cover art full-bleed on page 1 (`assets/cover.jpg`, 7 × 10 in, `object-fit: cover`), then the typographic half-title (accent band down the left), colophon page, Contents
(front-matter parts, then each chapter with its `##` sections; page numbers via
`target-counter`), then each front-matter part starting on a new page.

**Restraint rules.** One accent colour. No icons (a flask glyph on experiment headings was
tried and removed). No boxed "key takeaway" panels. No zebra tables. The assumption callout
is the only tinted box in body text; keep it that way so it retains its signal value.

## 4. Adding a new chapter — production checklist

1. Write `book/manuscript/NN-slug.md` with the three-comment header and `##` body.
2. Grep the file for lines > 80 chars inside fenced blocks; reflow them.
3. Check that every `*Assumption to notice:*`, `*Predict:*`, `*Decision N.*`, `**N.M**`
   is spelled exactly as in §2 so the build picks it up.
4. `make lint && make pdf && make site`, then render contact sheets and inspect: opener on a recto, TOC page
   numbers plausible, no overflowing code, no heading orphaned at page bottom, running
   heads correct.
5. If a `##` title is too long for the running head, shorten the title (the running head
   is `string-set` from the heading and cannot be overridden separately).
6. Update `BOOK["edition"]` in `fd/convert.py` when the part/draft label changes.

## 5. Known limitations

* WeasyPrint does not do real optical margin alignment or kerning-aware justification;
  occasional loose lines are expected in a draft. Final production could swap the engine
  (Prince, or Paged.js + Chromium) with the same HTML/CSS.
* Cross-origin `<link>` fonts are irrelevant here; fonts are local files referenced from
  `book.css` with paths relative to `production/`; `fd/pdf.py` sets `base_url` accordingly.
  The site copies the fonts into `out/site/fonts/`.
* Heading ids are namespaced per part (`fm-`, `ch1-`, `ch2-` …) so identical section
  names in different chapters do not collide in the TOC. If you hand-write cross-references
  as links, use those prefixed ids.

## 6. The web target

**Principle.** The site is a reading surface first. Same typefaces, same measure (42 rem
≈ 68–75 characters), same one accent, same device grammar as print. Interactive elements,
when they come, sit *inside* the reading column and the chapter reads completely without
them.

**Shell.** The reading column is centred at the measure on every width; nothing else is
persistent. The sidebar (book contents, 18 rem) is a drawer: on desktop it slides in when
the pointer touches the left 14 px edge or the top-left menu control, slides out when the
pointer leaves, and a pin in its header keeps it open (remembered as `fd-nav` in
localStorage; pinned pushes the column right instead of overlaying). The "on this page"
outline is fixed at the right (hidden below 1180 px), fades out after ~4 s without
scrolling, and returns on scroll or hover. Controls are two fixed icon buttons: menu
top-left, theme top-right; on phones they sit in a top bar that hides on scroll-down and
returns on scroll-up, with the book title in weight 500 between them. Below 860 px the
drawer overlays with a scrim and the pin is hidden.

**Index.** Centred cover art (≤ 20 rem wide), edition line, tagline, a single "Start
reading" link, then a one-column contents list: front-matter parts, then chapters as
number + title + opening question. Same layout at every width; simplicity is the point.

**Pages.** `index.html` (cover block + full contents with each chapter's question and
sections), one page per front-matter part (`fm-<slug>.html`), one page per chapter
(`<NN-slug>.html`, the manuscript filename). Headings keep the same namespaced ids as
print (`ch1-…`), so `chapter.html#ch1-section` deep links are stable. Prev/next pager at
the bottom of every page in reading order.

**Hierarchy on screen.** Running text uses `--body` (slightly softer than `--ink`); headings use `--ink` at weight 700; every `h2` carries a 2.5 rem accent rule above it. This is deliberate: on a screen, with no page rhythm, the print hierarchy read as flat. Headings have `scroll-margin-top: 1.5rem` (4 rem under the mobile top bar) so deep links land on the heading, not the previous paragraph.

**Theme.** Light by default, dark via `prefers-color-scheme`, overridable with the top-right toggle
(stored in `localStorage` under `fd-theme`; per-viewer convenience only). All colours are
tokens on `:root`; dark redefines them under `@media (prefers-color-scheme: dark)` guarded
by `:root:not([data-theme="light"])` and again under `:root[data-theme="dark"]`. Syntax
colours have separate dark values.

**Code.** Blocks scroll horizontally on narrow screens rather than wrapping. Tables do the
same. Diagrams keep their print treatment (rules above/below, muted ink).

**Fonts.** Copied from `production/fonts/lib/` into `out/site/fonts/` as OTF/TTF with
`font-display: swap`. Subsetting to WOFF2 is on the planned list; until then the site
ships ~2 MB of fonts, which is acceptable for a draft and not for launch.

**JavaScript.** One inline script in `fd/site.py`: theme, drawer hover/pin, outline idle fade and current-section highlight, scroll-aware top bar. It runs in `<head>` so the theme applies before first paint; anything that touches `document.body` must wait for `DOMContentLoaded`.
No framework, no bundler. Keep it that way until an interactive component needs more.

**Not in scope now.** Bookmarks, notes, progress, sync, accounts, comments, search.

## 7. Planned manuscript conventions (not yet implemented)

- `<!-- lab: ch1-exp-1 -->` immediately after an `### Experiment` heading: the site
  renders a prediction box and a "run it" link to a hosted lab page; print ignores it.
- `<!-- figure: script-timeline -->` before a diagram block: the site substitutes an
  interactive SVG; print keeps the monospace diagram.

Both must degrade to nothing in print and must be added to `fd/convert.py`, the fixture,
and §2 when implemented.
