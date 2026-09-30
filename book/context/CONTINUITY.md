# Continuity Ledger

What earlier chapters have established, promised, and deliberately deferred. **Read
before writing a chapter; append after.** This is how a chapter written in a fresh session
honours the book it belongs to without loading the earlier prose.

*Last updated after: Chapter 1.*

## Models and vocabulary already established (reuse; do not re-derive)

- **The five operations:** Predict, Explain, Break, Measure, Design. (Front matter)
- **Five kinds of claim:** specification-defined · standardized API · implementation
  detail · heuristic · teaching simplification. (Front matter, used throughout Ch. 1)
- **Observation / Hypothesis / Evidence / Decision** as debugging discipline. (Front
  matter, Ch. 1 failure story and measurement section)
- **Critical path:** total time is the longest dependency chain through concurrent work,
  not the sum of durations. Restructuring the graph beats shrinking a node. (Ch. 1)
- **"Fast hardware and localhost hide dependency structure."** The same code is a family
  of systems weighted differently per environment. (Ch. 1)
- **The dependency graph of a page load** (Ch. 1, "The Whole Graph"): streaming parser;
  preload scanner; parser-blocking scripts; render-blocking CSS (blocks paint and
  subsequent scripts, not parsing); async/defer/module semantics; DOMContentLoaded vs load;
  the rendering pipeline as a ladder (style → layout → paint → layerize → raster →
  composite; changes enter at different rungs with different costs); input path (compositor
  first, then main thread; hit test; capture/target/bubble; default action; next frame).
- **Browser process model** (browser process, network service, sandboxed renderers, GPU/Viz;
  main thread vs compositor thread), labelled as closest to Chromium.
- **Origin** = scheme + host + port, and the fact that it selects process, cookies, cache
  partition, service worker, and CORS behavior before any packet is sent.
- **"Visible ≠ interactive"** — pixels do not mean ready.
- **"It depends" is the beginning of the analysis** — then list variables.
- **Frontend dragon** as the name for the engineer with systems judgment (front matter).

## Terms defined (first use), so later chapters need not re-define

origin · recursive resolver · TTL · Happy Eyeballs (mentioned) · head-of-line blocking ·
SNI / ECH (mentioned) · 0-RTT · Alt-Svc (mentioned) · conditional request / ETag / 304 ·
heuristic freshness · cache partitioning by top-level site · 103 Early Hints · preload
scanner · parser-blocking / render-blocking · `fetchpriority` · `rel=preload` /
`preconnect` / `dns-prefetch` · Speculation Rules / prerender (mentioned) · tokenizer /
tree builder · display list · layer / compositor · raster tiles · hit testing · input
delay / processing time / presentation delay · INP (mentioned) · Navigation/Resource/Paint/
Event Timing (introduced, not exhaustively) · LCP / FCP (mentioned) · hydration (mentioned
in the decision section) · service worker (as a complication to navigation only).

## Promises made to later chapters (must be honoured)

| Promised in | Promise | Owed by |
|---|---|---|
| Ch. 1 close | Opening question "How wide is a `<div>`?"; deep treatment of layout, formatting contexts, fonts and `font-display`, layout shift, `contain` / `content-visibility`, layer heuristics, compositor-driven scrolling | Ch. 2 |
| Ch. 1 | The event loop, rendering opportunity, "single-threaded is incomplete", workers | Ch. 3 |
| Ch. 1 | Event dispatch, default actions, forms, focus in depth | Ch. 5 |
| Ch. 1 | Modules, module graphs, CORS fetching of modules, bundling; deploy warming of CDN edges (Decision 2) | Ch. 14 |
| Ch. 1 | Caching as consistency ("is this consistent with what the user just did"); redesign of data fetching; Decisions 3 and 6 revisited | Ch. 7 |
| Ch. 1 | Service workers, Cache Storage, offline architecture | Ch. 8 |
| Ch. 1 | Rigorous measurement: Performance Timeline APIs in detail, INP, percentiles, "measure ten thousand loads and believe the result" | Ch. 9 |
| Ch. 1 | Where computation should happen; SSR/streaming/hydration; Decision 1 revisited when routes multiply and a public status page appears; check the "What Would Change Your Mind" list against reality | Ch. 10 |
| Ch. 1 | Certificates, `Sec-Fetch-*`, sandboxing and site isolation as threat model, third-party script trust | Ch. 11 |
| Ch. 1 | Collecting timing data from real users | Ch. 16 |
| Ch. 1 | Atlas's informal decisions become proper decision records | Ch. 17 |
| Ch. 1 | Device and browser diversity, constrained hardware, bad networks | Ch. 18 |

## Deliberately deferred (do not steal)

Ch. 1 mentioned but did not treat: the event loop; CSS layout; cache consistency;
service-worker architecture; the threat model; statistics of measurement; SSR mechanics.
Each later chapter should likewise name what it leaves for others.

## Running motifs to keep alive

- Atlas's recurring question: *What assumption did Atlas make that is no longer true?*
- Each chapter ends by looking down one layer and forward to the next chapter's innocent-
  sounding question.
- The reader keeps a list of assumptions discovered to be false (front matter suggests it).

## Per-chapter log

### Chapter 1 — The Browser as a System (written 2026-09-29)
~20,000 words. Sections: The Question · The Naive Model · Breaking the Model · First
Principles, Part One: From Name to Bytes · An Interlude on Latency, Sums, and Critical
Paths · Inside the Platform · First Principles, Part Two: From Bytes to a Tree · Part
Three: From Tree to Pixels · Part Four: From Input to the Next Frame · The Whole Graph ·
Experiments (6) · Atlas: The First Load · A Failure Story · Measurement: Observations and
Theories · An Engineering Decision · What Would Change Your Mind? · Atlas: Decisions So
Far · The Layer Beneath · Exercises (24) · Further Exploration.
Assumptions surfaced: DNS on every request; connection is a fixed cost; requests run
sequentially; downloaded JS executes immediately; rendering happens once; pixels mean
ready; the URL is an address (it is a small program); all users start on the developer's
network.
