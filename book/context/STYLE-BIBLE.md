# Style Bible

How the book sounds and how it is put together. Read this in full before writing any
chapter. It is the contract that keeps twenty chapters written in twenty sessions
sounding like one author.

## Voice

Write for a thoughtful, experienced engineer sitting across a table. Warm, direct,
unhurried. Confident about mechanisms, candid about uncertainty. Curious rather than
authoritative. Occasionally dry; never jokey for its own sake. Respect the reader's
intelligence at every sentence: no cheerleading, no motivational filler, no "in today's
fast-paced world."

The book has a first-person plural voice ("we will build the model from the bottom")
and addresses the reader as "you." It never says "I."

## Prose, not structure

The book is paragraphs. Arguments are developed, not listed. A section breathes: it sets
up a question, works through it, and lands somewhere. Bullets appear only when a list is
truly a list (a set of parallel counterexamples, a set of options in a decision) and even
then each bullet is a full sentence or two. Never Definition / bullet list / Definition /
bullet list. Never a "Key takeaways" box. Never a summary that restates the section.

Vary sentence length. Use a short sentence for emphasis. Then move on.

Bold is rare: exercise numbers, the lead-in phrase of each counterexample in a "Break the
Model" list, and almost nothing else. Italics for defined terms on first use, for
emphasis, and for the recurring device labels.

## Banned phrases and patterns

Never write: "It's not just X, it's Y." · "The key takeaway is…" · "In today's modern
web…" · "Let's dive in." · "Let's unpack this." · "At its core…" · "As we can see…" ·
"This is crucial." · "This is important because…" · "genuinely" · "honestly" ·
"straightforward" · "delve" · "It's worth noting that…" · "Simply put…" ·
"In other words…" (more than once a chapter) · "In this section we will…"

Do not announce what you are about to explain. Explain it. Do not end sections with a
recap. Do not make every paragraph sound profound; most paragraphs should simply explain
difficult machinery clearly.

Run the banned-phrase grep from `QC-CHECKLIST.md` before finishing.

## The teaching loop, in practice

Ask before telling. Present the intuitive model with respect ("this is a good model")
before breaking it. When breaking it, use concrete, specific counterexamples, each of
which a reader could reproduce. Let an incomplete model stand for a page before showing
where it fails. Build the deeper model from causes ("the parser must stop here *because*
the script might call document.write, and that matters *because*…"), not from rules.

Escalating examples: show a tiny piece of code, ask what it does, answer, alter it, ask
what changed, alter again. The `document.body` sequence in Chapter 1 is the template.

Experiments: give exact setup, then `*Predict:*`, then what the reader should find. Never
reveal the result before the prediction prompt.

## Recurring devices (exact spellings — the build detects these)

- `*Assumption to notice:* we assumed X. Actually Y.` — one paragraph, lowercase after
  the label (the build capitalizes). Two to six per chapter.
- `*Predict:* what happens when…?` — in experiments and escalating examples.
- `*Decision N. Short title.* Chosen because… Known weakness… Revisit when…` — in the
  Atlas decisions section. Numbering continues across chapters (see `ATLAS-STATE.md`).
- Observation / Hypothesis / Evidence / Decision — used explicitly in failure stories and
  measurement sections, as plain words in prose or as a short labelled sequence. Not
  everywhere.
- The five kinds of claim: *specification-defined*, *standardized API*, *implementation
  detail*, *heuristic*, *teaching simplification*. Label Chromium/WebKit/Gecko specifics as
  such. Say "this is a teaching simplification" when it is.
- "It depends. But 'it depends' is the beginning of the analysis, not the end." — then
  name the variables. Use the pattern; do not quote the sentence verbatim more than once
  per chapter.
- Translate machinery into user experience regularly: "I clicked and nothing happened."

## Chapter skeleton

`## The Question` (a scene) · `## The Naive Model` · `## Breaking the Model` ·
`## First Principles…` (one or several, may be "Part One/Two…") · `## Inside the
Platform` · `## Experiments` (each `### Experiment N: Title`) · `## Atlas: …` ·
`## A Failure Story` · `## Measurement…` · `## An Engineering Decision` · `## What Would
Change Your Mind?` · `## Atlas: Decisions So Far` · a closing `##` that looks down to the
next layer and forward to the next chapter · `## Exercises` · `## Further Exploration`.

Headings may be renamed or merged where the prose demands; `## Exercises` and
`## Further Exploration` must keep those exact names. Section titles ≤ 45 characters.

Target length: 18,000–24,000 words for a major chapter. Depth over coverage.

## Exercises

`### Prediction`, `### Explanation`, `### Debugging`, `### Experiment`, `### Design`,
`### Source exploration`. Numbered `**N.M**` (chapter.number). Mark difficult ones ◆ and
open-ended ones ◆◆. 20–25 exercises. No recall questions. Design exercises present
competing requirements. Source-exploration exercises name a specific spec/RFC/trace and
ask a precise question.

## Further exploration

`### Read next` · `### Read deeper` · `### Inspect real systems` · `### Optional rabbit
holes`. Six to twelve items total, each as a short paragraph saying *why* it is worth the
time. No bare link lists. Prefer primary sources.

## Code and diagrams

Code small enough to reason about; plain HTML/CSS/JS over framework code unless the
framework's behavior is the subject. Code reveals behavior; it is never there to fill
space. Max 80 columns. Diagrams in fenced blocks with no language, box-drawing
characters, ≤ 86 columns, ≤ 35 lines, only when they show causality (dependency,
timeline, pipeline, waterfall). No decorative diagrams.

Mathematics only when it clarifies (a latency sum and why it fails; a critical path).
Never decorative equations.

## Atlas

Atlas must feel real: specific numbers, specific files, specific failures. Never
overbuilt for the current chapter. Every chapter: apply the chapter's model to Atlas,
find a realistic problem, measure it, change the system, measure again, record decisions.
Read `ATLAS-STATE.md` first; update it last.

## Continuity

Before writing, read `CONTINUITY.md`: promises earlier chapters made to this one, models
and terms already established (reuse them; do not re-derive them), and things deliberately
deferred to later chapters (do not steal them). After writing, add this chapter's
promises, new models, and new terms.

## Sources and honesty

Verify technical claims against primary sources. Hedge where browsers differ ("in
Chromium…", "at the time of writing…", "test this in the browsers you care about"). Never
invent measurements presented as real-world data; illustrative numbers must be internally
consistent with the dependency structure being described, and it is fine to say they are
illustrative.
