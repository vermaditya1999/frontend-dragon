"""
Shared Markdown → HTML conversion for Frontend Dragon.

Both the PDF and the site builders use this module, so the manuscript conventions
(documented in production/DESIGN-GUIDELINES.md) are interpreted in exactly one place.
"""
import glob, html, os, re
import markdown
from markdown.extensions.toc import TocExtension
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

BOOK = {
    "title": "Frontend Dragon",
    "subtitle": "Engineering the Web from First Principles",
    "tagline": ("A systems-oriented book for experienced frontend engineers who want to develop "
                "senior, staff, and principal-level judgment: to reason about unfamiliar problems "
                "from first principles, investigate failures from evidence, and defend consequential decisions."),
    "edition": "Draft manuscript · Part One: The Platform",
    "year": "2026",
}

# ----------------------------------------------------------------------------
# Markdown → HTML
# ----------------------------------------------------------------------------

def md_to_html(text):
    md = markdown.Markdown(extensions=[
        "tables", "fenced_code", "smarty",
        TocExtension(anchorlink=False, permalink=False, toc_depth="1-3"),
    ], output_format="html5")
    return md.convert(text), md.toc_tokens


_FORMATTER = HtmlFormatter(nowrap=True)
_LANG_ALIASES = {"js": "javascript", "ts": "typescript", "sh": "bash", "http": "http"}


def _highlight_code(m):
    lang = m.group(1)
    code = html.unescape(m.group(2))
    try:
        lexer = get_lexer_by_name(_LANG_ALIASES.get(lang, lang), stripall=False)
    except Exception:
        return m.group(0)
    body = highlight(code, lexer, _FORMATTER).rstrip("\n")
    return f'<div class="codehilite"><pre><code class="language-{lang}">{body}</code></pre></div>'


def _diagram_block(m):
    body = m.group(1)
    width = max((len(html.unescape(l)) for l in body.split("\n")), default=0)
    cls = "diagram wide" if width > 92 else "diagram"
    return f'<pre class="{cls}"><code>{body}</code></pre>'


def _mark_long_pre(m):
    attrs, body = m.group("attrs"), m.group("body")
    if body.count("\n") > 18 and "class=" not in attrs:
        return f'<pre class="long"{attrs}>{body}</pre>'
    return f"<pre{attrs}>{body}</pre>"


def postprocess(h):
    """Apply the book's recurring devices. Patterns must match DESIGN-GUIDELINES.md §2."""
    h = re.sub(r'<pre><code class="language-(\w+)">(.*?)</code></pre>', _highlight_code, h, flags=re.S)
    h = re.sub(r'<pre><code>(.*?)</code></pre>', _diagram_block, h, flags=re.S)
    h = re.sub(r'<p><em>Assumption to notice:</em>\s*(\w)',
               lambda m: '<p class="assumption"><em>Assumption to notice</em>' + m.group(1).upper(), h)
    h = re.sub(r'<p><em>Predict:</em>\s*(\w)',
               lambda m: '<p class="predict"><em>Predict:</em> ' + m.group(1).upper(), h)
    h = re.sub(r'<pre(?P<attrs>[^>]*)>(?P<body>.*?)</pre>', _mark_long_pre, h, flags=re.S)
    h = re.sub(r'<p><em>(Decision \d+\..*?)</em>', r'<p class="decision"><em>\1</em>', h)
    h = re.sub(r'<p><strong>(\d+\.\d+)</strong>\s*', r'<p class="exercise"><strong>\1</strong>', h)
    h = re.sub(r'<h3 id="([^"]*)">(Experiment \d+[^<]*)</h3>', r'<h3 class="experiment" id="\1">\2</h3>', h)
    h = h.replace("<hr />", '<hr class="section-break" />').replace("<hr>", '<hr class="section-break" />')
    return h


def prefix_ids(h, toks, prefix):
    """Namespace heading ids so identical headings in different parts never collide."""
    h = re.sub(r'<(h[1-4]) id="([^"]+)"', lambda m: f'<{m.group(1)} id="{prefix}{m.group(2)}"', h)
    def walk(ts):
        for tk in ts:
            tk["id"] = prefix + tk["id"]
            walk(tk.get("children", []))
    walk(toks)
    return h


def wrap_special_sections(h, prefix=""):
    """Wrap `## Exercises` and `## Further Exploration` in classed divs."""
    def wrap(h, hid, cls):
        hid = prefix + hid
        m = re.search(rf'<h2 id="{hid}">', h)
        if not m:
            return h
        start = m.start()
        nxt = re.search(r'<h2 id="', h[m.end():])
        end = m.end() + nxt.start() if nxt else len(h)
        return h[:start] + f'<div class="{cls}">' + h[start:end] + "</div>" + h[end:]
    h = wrap(h, "further-exploration", "further")
    h = wrap(h, "exercises", "exercises")
    return h

# ----------------------------------------------------------------------------
# Manuscript loading
# ----------------------------------------------------------------------------

def parse_chapter_meta(text):
    meta = dict(re.findall(r'<!--\s*(\w+):\s*(.*?)\s*-->', text))
    body = re.sub(r'^(\s*<!--.*?-->\s*)+', "", text, count=1, flags=re.S)
    return meta, body


def load_front_matter(path):
    """Returns a list of parts: dicts with id, title, html."""
    text = open(path, encoding="utf-8").read()
    h, toks = md_to_html(text)
    h = prefix_ids(postprocess(h), toks, "fm-")
    pieces = re.split(r'(?=<h1 id=")', h)
    pieces = [re.sub(r'(<hr class="section-break" />\s*)+$', "", p.strip()) for p in pieces if p.strip()]
    entries = [(t["id"], t["name"]) for t in toks if t["level"] == 1]
    parts = []
    for (pid, name), piece in zip(entries, pieces):
        parts.append({"id": pid, "title": name, "html": piece})
    return parts


def load_chapter(path):
    """Returns a dict with num, title, question, html, sections [(id, name)], slug."""
    text = open(path, encoding="utf-8").read()
    meta, body = parse_chapter_meta(text)
    if "chapter" not in meta or "title" not in meta:
        raise SystemExit(f"{path}: missing <!-- chapter: N --> / <!-- title: ... --> header (see DESIGN-GUIDELINES.md §2)")
    num, title, question = meta["chapter"], meta["title"], meta.get("question", "")
    h, toks = md_to_html(body)
    h = prefix_ids(postprocess(h), toks, f"ch{num}-")
    h = wrap_special_sections(h, f"ch{num}-")
    sections = [(t["id"], t["name"]) for t in toks if t["level"] == 2]
    slug = os.path.splitext(os.path.basename(path))[0]
    return {"num": num, "title": title, "question": question, "html": h,
            "sections": sections, "slug": slug, "anchor": f"chapter-{num}"}


def load_manuscript(ms_dir):
    fm_path = os.path.join(ms_dir, "00-front-matter.md")
    if not os.path.exists(fm_path):
        raise SystemExit(f"missing {fm_path}")
    chapter_paths = sorted(p for p in glob.glob(os.path.join(ms_dir, "*.md"))
                           if not p.endswith("00-front-matter.md"))
    return load_front_matter(fm_path), [load_chapter(p) for p in chapter_paths]


def lint_manuscript(ms_dir, code_max=80, diagram_max=86):
    """Report fenced blocks wider than the print measure allows. Returns a list of messages."""
    problems = []
    for path in sorted(glob.glob(os.path.join(ms_dir, "*.md"))):
        text = open(path, encoding="utf-8").read()
        for m in re.finditer(r'```(\w*)\n(.*?)```', text, re.S):
            lang, body = m.group(1), m.group(2)
            limit = code_max if lang else diagram_max
            width = max((len(l) for l in body.split("\n")), default=0)
            if width > limit:
                line = text[: m.start()].count("\n") + 1
                kind = f"code ({lang})" if lang else "diagram"
                problems.append(f"{os.path.basename(path)}:{line}: {kind} block is {width} cols wide (limit {limit})")
    return problems
