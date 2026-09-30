<!-- chapter: 1 -->
<!-- title: The Fixture Chapter -->
<!-- question: Does every device in the book render correctly? -->

## The Question

This chapter is not part of the book. It is a fixture that exercises every typographic device the manuscript can contain, in about fifteen hundred words, so that the print and web pipelines can be debugged cheaply. If a device is added to the book, add an instance of it here and to `DESIGN-GUIDELINES.md`.

It is 9:07 on a Tuesday morning. A paragraph long enough to wrap several times, so that justification, hyphenation, and line spacing can be judged. Sentences vary in length. Some are short. Others carry on for a while, with subordinate clauses and the occasional parenthetical (like this one), to see how the engine handles a full measure of running text before the next paragraph begins.

*Assumption to notice:* we assumed the callout renders with its label in small caps and its first letter capitalized by the build. It should.

## Escalating Examples

Consider this document.

```html
<!doctype html>
<html>
<head>
  <script>
    console.log(document.body);
  </script>
</head>
<body>
  Hello
</body>
</html>
```

What does the script log? Commit to an answer before reading on.

It logs `null`. Now a JavaScript block, to check keyword and string colouring:

```js
const url = new URL(req.url, "http://localhost");
const delay = Number(url.searchParams.get("delay") ?? 0);
await new Promise(r => setTimeout(r, delay));
// a comment, which should be muted and italic
```

And a long code block, which should be allowed to break across pages in print and to scroll horizontally on the web if a line were too wide (none is; the lint forbids it):

```js
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname } from "node:path";

const types = {
  ".html": "text/html", ".css": "text/css",
  ".js": "text/javascript", ".json": "application/json",
};

createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const delay = Number(url.searchParams.get("delay") ?? 0);
  await new Promise(r => setTimeout(r, delay));
  try {
    const body = await readFile("." + url.pathname);
    res.writeHead(200, {
      "Content-Type": types[extname(url.pathname)] ?? "text/plain",
      "Cache-Control": "no-store",
    });
    res.end(body);
  } catch {
    res.writeHead(404); res.end();
  }
}).listen(8080);
```

## Diagrams and Mathematics

A diagram is a fenced block with no language. It renders without a background, with thin rules, in muted ink.

```
   client                              server
     │── SYN ─────────────────────────▶│
     │◀──────────────────── SYN-ACK ───│    1 RTT: TCP
     │── ACK ─────────────────────────▶│
     │── ClientHello (key share) ─────▶│
     │◀── ServerHello, cert, Finished ─│    1 RTT: TLS 1.3
     │── Finished + HTTP request ─────▶│
```

A timeline with block glyphs:

```
time →   0         300       500       700       950
HTML     ██████████
CSS         ████████
bundle      ████████████████
API                          ██████████
                                       ▲ usable at ~950 ms
```

An equation, also as a diagram block:

```
T_navigation ≈ T_DNS + T_connect + T_TLS + T_request
             + T_server + T_transfer + T_processing
```

*Assumption to notice:* we assumed all diagrams are narrower than 86 columns. The lint checks this.

## Tables

| Environment | First paint | Usable | Bundle transfer | API |
|---|---|---|---|---|
| Localhost, warm | 40 ms | 180 ms | 0 | 8 ms |
| Production, cold | 600 ms | 1,300 ms | 420 ms | 190 ms |
| Distant 4G phone, cold | 980 ms | 4,200 ms | 1,400 ms | 600 ms |

Tables are set in the sans, with thin rules and no zebra striping.

## Experiments

### Experiment 1: The blocking script

Create a page with a slow script in the head.

*Predict:* when does the heading appear? What does the Network panel show?

What you should find: the heading appears after the script arrives.

### Experiment 2: What CSS actually blocks

*Predict:* when does the inline script run?

## A Section With a Break

Text before the break.

---

Text after the break. The break renders as three centred dots.

### A level-three heading

#### A level-four heading, italic run-in

Paragraph following a level-four heading.

## Atlas: Decisions So Far

*Decision 1. Client-side rendering with a static shell.* Chosen for simplicity. Known weakness: the interface appears only after the bundle runs. Revisit in Chapter 10.

*Decision 2. Content-hashed immutable assets.* Chosen so assets cache indefinitely. Revisit in Chapter 14.

## The Layer Beneath

A closing section. It should look like ordinary prose. The next chapter begins with a question that sounds as innocent as this chapter's: does the fixture cover everything?

## Exercises

Exercises are grouped by the operation they practice. Those marked ◆ are difficult; those marked ◆◆ are open-ended.

### Prediction

**1.1** A page contains a `<link rel="stylesheet">` and an inline `<script>`. What is the title at 500 ms? This exercise is long enough to wrap so that the hanging indent can be checked against a second and third line of text.

**1.2** ◆ Two `<script defer>` tags appear in the head. In what order do they execute?

### Design

**1.3** ◆◆ Choose an architecture and justify it against each requirement.

Some exercises carry a code block:

```html
<head>
  <link rel="stylesheet" href="a.css">
  <script src="b.js"></script>
</head>
```

## Further Exploration

### Read next

*High Performance Browser Networking* by Ilya Grigorik. The best single treatment of the network layer for web engineers.

### Read deeper

The WHATWG HTML standard, sections on parsing and scripting. Search for the algorithm you need; do not read linearly.

### Optional rabbit holes

The Happy Eyeballs RFCs, for the pleasure of reading a specification whose whole purpose is to race two things.
