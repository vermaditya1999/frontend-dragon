# Atlas — Current State

The running state of the book's laboratory application. **Read before writing a chapter.
Update as the last step of writing a chapter.** Keep it under ~700 words; this file is
what makes Atlas continuous across sessions written months apart.

*Last updated after: Chapter 1.*

## What Atlas is

An incident-management interface. Users open a list of incidents, open one, read what is
known, and change its status. Written in TypeScript; React for the UI where a framework is
needed. Code samples in the book are kept small; the "companion repository" is referred to
but not reproduced.

## Current architecture (end of Chapter 1)

- **Single-page application, client-rendered.** Static HTML shell served from a CDN.
- **Files:** `index.html` (shell), `/assets/atlas.<hash>.css`, `/assets/atlas.<hash>.js`
  (~280 KB compressed before splitting; React + router + ~200 lines of app code), a
  self-hosted web font (Inter), one API.
- **Routes:** `/` (incident list) and `/incidents/:id` (detail with a status dropdown).
  The detail route is now a separately loaded chunk (~90 KB removed from the initial bundle).
- **API:** `GET /api/incidents` returns a JSON array; `PATCH /api/incidents/:id` changes
  status. Same origin as the app, behind the CDN, which passes API traffic to an
  application server in Virginia (us-east). API responses are `Cache-Control: no-store`.
- **Caching:** assets are content-hashed and `public, max-age=31536000, immutable`; the
  HTML shell is `no-cache` (revalidated every load; changes on every deploy because hashes
  change).
- **Head of `index.html` now contains:** `<link rel="preload" href="/api/incidents"
  as="fetch" crossorigin>` so the first data request overlaps the bundle download;
  self-hosted font with `<link rel="preload" as="font">`; the font stylesheet is
  non-render-blocking with a system-font fallback.
- **Team:** two engineers. No rendering server. No service worker. No auth yet.

## Target environment for performance claims

A mid-range Android phone on 4G with 150 ms RTT, ~9,000 km from the origin, cold cache.
All performance numbers in the book are stated against this unless otherwise noted.
Current numbers there: first paint ≈ 520 ms (empty shell), usable ≈ 2,400 ms.
Requirement: usable ≤ 2,000 ms. Remaining critical path: HTML → bundle transfer
(~950 ms) → bundle execution (~450 ms) → render.

Other environments measured in Chapter 1 (usable): localhost warm 180 ms; production
warm 450 ms; production cold 1,300 ms.

## Decisions on record

Numbering continues across chapters. Format: number, title, why, known weakness, revisit.

1. **Client-side rendering with a static HTML shell from a CDN.** Simplicity of deployment;
   one route and one API call do not justify a rendering server. Structural cost: interface
   appears only after bundle transfer + execution. *Revisit when routes multiply or an
   anonymous must-render-instantly route appears (Chapter 10).*
2. **Content-hashed immutable assets; `no-cache` HTML shell.** Weakness: every deploy
   cold-starts every CDN edge for the new hashes. *Revisit: deploy warming, Chapter 14.*
3. **Initial API request preloaded from the HTML.** Removed the API from the critical
   path with one line. Weakness: duplicates knowledge of the route's data dependency between
   shell and app; will drift. *Revisit: Chapter 7.*
4. **Fonts self-hosted and non-render-blocking with a system fallback.** After the
   Singapore incident. No third-party origin on the render-blocking path. Expected to stand.
5. **Target performance environment is the distant 4G phone, cold cache.** Localhost
   measurements were found uninformative.
6. **Atlas assumes the data it fetches is the current state of the incident.** Inherited,
   unexamined. *Chapter 7 examines it.*

## Assumptions still standing (to be broken later)

- One user edits an incident at a time. (Ch. 7/8)
- The user is online. (Ch. 8)
- The browser is a recent Chrome on a laptop; the network is fast. (Partly broken in Ch. 1;
  device/browser diversity in Ch. 18)
- Every user may see every incident; there is one tenant. (Ch. 11)
- The list is small enough to render in full. (Ch. 2/9)
- The deploy reaches everyone at once. (Ch. 14/17)
- Everyone reads English, left to right. (Ch. 18)
- The click handler is attached by the time the user can see the button. (Ch. 3/5/9)

## Incidents in Atlas's history

- **The Singapore blank page (Ch. 1).** Third-party font stylesheet on the render-blocking
  path, served from a European edge to Asia-Pacific resolvers; compounded by cold CDN
  edges after a deploy. Fixed by Decision 4. Blank-page time there now ≈ 700 ms.

## Open threads

- Bundle still ~190 KB on the critical path; 2,000 ms target not yet met.
- "Option C" (stream the shell before data) noted as the likely next architecture when
  a public status page arrives.
- Deploy warming of CDN edges not addressed.
