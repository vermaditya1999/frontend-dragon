# Chapter Specifications

One entry per chapter, from the book brief. When a chapter is about to be written, its
entry here is the *minimum* scope; the person commissioning the chapter may add a more
detailed spec (Chapter 1's detailed spec is preserved at the end as the exemplar of how
much detail a chapter brief can carry).

Status legend: ✅ written · 🟡 in progress · ⬜ not started

---

## 1. The Browser as a System ✅

Navigation, URLs, DNS, connection establishment, TLS, HTTP, browser processes, parsing,
DOM/CSSOM construction, script execution, rendering, input, and the dependency graph
connecting everything. Reader finishes with a coherent mental model of what actually
happens between entering a URL and interacting with a page.

## 2. Layout, Typography, and Pixels ⬜

Intrinsic sizing, containing blocks, formatting contexts, flexbox, grid, overflow,
typography, replaced elements, responsive layout, paint, compositing, GPU layers, and
designing for content whose size cannot be predicted.
Opening question (promised at the end of Chapter 1): *How wide is a `<div>`?*

## 3. JavaScript over Time ⬜

Execution contexts, identity, mutation, closures, prototypes, tasks, microtasks, promises,
the event loop, object lifetimes, garbage collection, memory ownership, leaks, workers, and
why describing JavaScript as simply "single threaded" is incomplete.
Chapter 1 promised: the full event loop and rendering-opportunity treatment lives here.

## 4. Modeling Application Behavior ⬜

State, derived state, invariants, algebraic data types, TypeScript as a modeling tool,
state machines, transitions, reducers, event-sourcing ideas, and making invalid states
difficult or impossible to represent.

## 5. Interaction, Forms, and Accessibility ⬜

DOM events, propagation, default actions, keyboard input, pointer input, forms, focus,
semantics, ARIA, assistive technologies, screen readers, modal behavior, complete user
journeys. Chapter 1 promised: event dispatch, default actions, focus in depth.

## 6. Framework Execution Models ⬜

Fine-grained reactivity, signals, virtual DOMs, dependency graphs, scheduling, batching,
memoization, effects, component lifetimes, ownership, and the tradeoffs behind React,
Solid, Vue, Svelte. Not a popularity contest.

## 7. Asynchronous Data and Server State ⬜

Request races, cancellation, deduplication, retries, cache identity, freshness,
invalidation, optimistic updates, conditional requests, HTTP caching semantics, stale data,
consistency, and what server-state libraries fundamentally solve.
Chapter 1 promised: caching consistency ("is this consistent with what the user just
did"), Atlas Decision 3 (preloaded API request) and Decision 6 (data assumed current)
are revisited here.

## 8. Persistence, Realtime, Offline, and Collaborative State ⬜

Cookies, localStorage, IndexedDB, Cache Storage, service workers, BroadcastChannel,
WebSockets, SSE, durable intent, reconnects, retries, idempotency, ordering, conflict
resolution, optimistic interfaces, synchronization, CRDT concepts, convergence.
Chapter 1 promised: service workers and offline architecture in depth.

## 9. Performance Engineering ⬜

Workload models, network waterfalls, main-thread contention, long tasks, latency
distributions, scheduling, responsiveness, memory, rendering cost, workers, profiling,
measurement methodology, percentiles, statistical noise, performance budgets.
Chapter 1 promised: detailed use of the Performance Timeline APIs, INP, and how to
measure ten thousand loads and believe the result.

## 10. Rendering across Client, Server, and Edge ⬜

CSR, SSR, SSG, streaming, hydration, partial hydration, islands, resumability, server
components as an execution model, CDN caching, edge computation, navigation, prefetching,
where computation should occur. Chapter 1 promised: Atlas Decision 1 (CSR) is revisited
here when routes multiply and a public status page appears; the "what would change your
mind" list from Chapter 1 is checked against what happened.

## 11. Security and Trust Boundaries ⬜

Origins, browser isolation, CSP, CORS, XSS, CSRF, cookies, sessions, tokens,
authentication, authorization, tenant isolation, untrusted HTML, third-party scripts,
dependency trust, frontend threat modeling. Chapter 1 promised: certificates,
`Sec-Fetch-*` headers, sandboxing and site isolation as a threat model.

## 12. Testing Systems, Not Functions ⬜

Unit, integration, browser, end-to-end, property-based, model-based testing; deterministic
time; generated event histories; network failure; race conditions; fault injection;
fuzzing; visual regressions; accessibility testing; deciding what is worth testing.

## 13. Component, API, and Design-System Engineering ⬜

Contracts, composition, controlled/uncontrolled APIs, extensibility, design tokens,
accessibility guarantees, backwards compatibility, versioning, deprecation, evolving
shared interfaces used by many engineers.

## 14. Build and Delivery Systems ⬜

ES modules, module resolution, package graphs, dependency management, TypeScript
compilation, bundlers, tree shaking, code splitting, source maps, transforms,
minification, reproducible builds, dependency security, hashing, caching, CDN delivery,
deployment correctness. Chapter 1 promised: modules in depth; Atlas Decision 2 (cold CDN
edges on deploy) addressed here.

## 15. Frontend Architecture ⬜

Boundaries, coupling, cohesion, ownership, feature architecture, shared infrastructure,
monorepos, microfrontends, dependency direction, change propagation, Conway's Law,
organizational constraints, architecture as management of future change.

## 16. Production Observability and Debugging ⬜

Logs, traces, metrics, telemetry, frontend error reporting, user-impact measurement,
session reconstruction, source maps, correlation IDs, distributed debugging, incident
response, reasoning from incomplete evidence, separating hypotheses from observations.
Chapter 1 promised: collecting timing data from real users.

## 17. Technical Strategy and Migration ⬜

RFCs, ADRs, decision records, cost models, prototypes, migration graphs, compatibility
layers, strangler patterns, feature flags, incremental adoption, rollout, rollback,
success criteria, deleting obsolete systems, and when a migration should *not* happen.
Chapter 1 promised: Atlas's informal decisions become proper decision records here.

## 18. The Global, Heterogeneous Web ⬜

Unicode, i18n, l10n, time zones, calendars, currencies, number formatting, input methods,
bidirectional text, browser differences, device capabilities, touch, reduced motion,
constrained hardware, unreliable networks, progressive enhancement, graceful degradation.

## 19. Atlas: Production Release ⬜

Bring the system together. Reviews: accessibility, performance, security, authorization,
tenant isolation, offline behavior, realtime behavior, observability, browser
compatibility testing, failure recovery testing, production readiness.

## 20. Architecture Defense ⬜

Defend Atlas in a demanding architecture review: justify major decisions, present
evidence, acknowledge uncertainty, respond to competing proposals, design a migration,
rehearse rollout and rollback, conduct an incident exercise, distinguish facts from
assumptions, explain what available evidence cannot establish. Judgment, not trivia.

---

## Exemplar: the detailed spec Chapter 1 was written from

Kept so future chapter briefs can be written at the same level of detail.

**Opening question:** What happens when you enter a URL and press Enter? Do not answer
with the interview-style sequence (DNS → TCP → HTTP → HTML → CSS → JS → render); show why
that model is useful but deeply incomplete.

**Model to develop, covering at least:** URL parsing, schemes, origins, DNS, IP
addressing (conceptual), connection establishment, TCP concepts, QUIC/HTTP/3, TLS,
certificates (conceptual), HTTP requests/responses/headers, redirects, caching,
connection reuse, HTTP/2 multiplexing, browser networking architecture, browser and
renderer processes, sandboxing (conceptual), navigation lifecycle, HTML streaming,
tokenization, parsing, DOM construction, preload scanning, CSS discovery, CSSOM,
blocking resources, JavaScript discovery/execution, parser-blocking scripts, async,
defer, modules, fetch priority, DOMContentLoaded, load, style, layout, paint,
compositing, rasterization, display, user input, hit testing, event dispatch,
interaction-to-next-frame.

**Must clearly distinguish:** sequential dependencies, concurrent work, browser
heuristics, specification-defined behavior, implementation details, teaching
simplifications. Show the dependency graph; make concurrency visible.

**Required teaching rhythm:** The Question (a scene: 9:07 a.m., laptop, Enter) → Naive
Model → Break the Model (rendering before response completes; script delays parsing; late
CSS; cached resources skip the path; HTTP/2 changes scheduling; service worker
intercepts; interaction during load) → First Principles → Inside the Platform →
Experiments (disable cache and read the waterfall; throttle; normal/async/defer/module;
blocking CSS; streamed HTML; timing entries; first vs repeat visit; redirect; DCL vs
load — predict before revealing) → Atlas (shell + bundle + styles + fonts + API; analyze
startup; a bundle-blocks-rendering problem; measure, change, compare) → Failure Story
(healthy deploy, distant region sees a blank screen; investigate, don't announce) →
Measurement (observation vs theory; TTFB 700 ms ≠ "server slow"; timing APIs) →
Engineering Decision (A: larger bundle CSR; B: SSR the shell; C: stream shell before data;
D: CSR + aggressive preload/cache — no universal winner) → What Would Change Your Mind →
Exercises → Further Exploration.

**Required escalating code example:** `console.log(document.body)` in head → in body →
with `defer`.

**Required diagrams (ASCII/Mermaid acceptable):** browser architecture; navigation path;
DNS + connection setup; streaming parser timeline; parser/script/CSS interaction;
rendering pipeline; network waterfall; input-to-frame; end-to-end dependency graph.

**Required math:** the naive latency sum, then why it fails (overlap), introducing
critical-path thinking.

**Atlas target by end of chapter:** minimal real app (Browser → CDN → HTML → CSS → JS
bundle → incident API → render), analyzed under warm cache, cold cache, localhost, distant
network, slow CPU; ends with a few documented decisions to revisit later.

**Assumptions to surface:** DNS on every request; HTML must finish before parsing;
downloaded JS executes immediately; rendering happens once; all users start cold; requests
run sequentially; pixels mean ready.
