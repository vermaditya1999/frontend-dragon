# Quality-Control Checklist (run before a chapter is called done)

## Mechanical (run these)

```
# banned phrases — must print nothing
grep -n -i -E "it's not just|key takeaway|in today's|let's dive|let's unpack|at its core|as we can see|this is crucial|this is important because|genuinely|honestly|straightforward|delve|worth noting|simply put|in this section we" book/manuscript/NN-*.md

# structure: reserved headings present and spelled exactly
grep -n -E "^## (Exercises|Further Exploration)$" book/manuscript/NN-*.md

# devices spelled so the build detects them
grep -c "^\*Assumption to notice:\*" book/manuscript/NN-*.md     # expect 2–6
grep -c "^\*Predict:\*" book/manuscript/NN-*.md                  # expect ≥ 6
grep -c "^\*Decision [0-9]+\." book/manuscript/NN-*.md            # expect ≥ 2
grep -c "^\*\*[0-9]+\.[0-9]+\*\*" book/manuscript/NN-*.md         # expect 20–25

# width limits (code ≤ 80, diagrams ≤ 86)
make lint

# bullets: the book is prose. Count list items; if this is large, rewrite.
grep -c -E "^\s*[-*] " book/manuscript/NN-*.md

# word count (target 18k–24k for a major chapter)
wc -w book/manuscript/NN-*.md
```

## Editorial (read and judge)

Remove: repetitive explanations · filler · AI-style transitions · redundant summaries ·
excessive bullet lists · unexplained jargon · shallow claims · fake certainty · framework
tribalism · generic motivational language · announcements of what is about to be explained.

Check that:

- each section teaches something meaningful and could not be cut without loss;
- causal relationships are explicit (*because*, not *note that*);
- examples are technically correct and small enough to reason about;
- experiments actually reveal the stated principle, and the prediction comes before the reveal;
- implementation details are labelled as such; nothing Chromium-specific is stated as a law;
- Atlas feels real (specific numbers, files, failures) and is not overbuilt;
- the engineering decision has no declared universal winner and names its variables;
- "What Would Change Your Mind" lists concrete evidence, both directions;
- exercises are hard, varied by category, and some are open-ended;
- further exploration explains *why* each item is worth the time;
- prose flows; sentence length varies; no paragraph exists only to sound profound;
- an experienced frontend engineer would learn something surprising;
- the chapter uses models from `CONTINUITY.md` rather than re-deriving them, and does
  not steal topics deferred to later chapters;
- the chapter ends by looking down a layer and forward to the next chapter's question.

Most importantly: would a technically curious engineer voluntarily keep reading?
If not, rewrite.

## Bookkeeping (do not skip)

- `book/context/ATLAS-STATE.md` updated: architecture, numbers, decisions (numbering
  continued), assumptions broken/still standing, incidents, open threads.
- `book/context/CONTINUITY.md` updated: new models/terms, promises made, deferred topics,
  per-chapter log entry.
- `book/context/CHAPTER-SPECS.md` status flipped to ✅.
- `make pdf && make site` succeed; contact sheet inspected for overflow and orphaned headings.
- `AGENTS.md` decisions log appended if any process decision was made.
