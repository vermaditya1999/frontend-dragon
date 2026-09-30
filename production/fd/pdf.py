"""PDF target: one paged HTML document → WeasyPrint."""
import html, os
from .convert import BOOK

def _cover():
    b = BOOK
    return f'''
<div class="cover-image"><img src="assets/cover.jpg" alt=""></div>
<div class="cover">
  <div class="band"></div>
  <div class="inner">
    <div class="series">{b["edition"]}</div>
    <div class="title">{b["title"]}</div>
    <div class="subtitle">{b["subtitle"]}</div>
    <div class="rule"></div>
    <div class="tagline">{b["tagline"]}</div>
  </div>
  <div class="foot">{b["year"]}</div>
</div>'''


def _colophon():
    return f'''
<div class="colophon"><div class="colophon-inner">
  <p><strong>{BOOK["title"]}: {BOOK["subtitle"]}</strong></p>
  <p>{BOOK["edition"]}. This is a working draft and is subject to revision. Technical claims about browser behavior are labelled, where possible, as specification-defined, standardized API, implementation detail, heuristic, or teaching simplification; readers are encouraged to verify against the primary sources listed at the end of each chapter and against the browsers they care about.</p>
  <p>Body text is set in Source Serif 4, headings in Source Sans 3, and code in JetBrains Mono. Typeset with WeasyPrint.</p>
</div></div>'''


def _toc(parts, chapters):
    fm = "".join(f'<li class="fm"><a href="#{p["id"]}">{p["title"]}</a></li>' for p in parts)
    ch = ""
    for c in chapters:
        subs = "".join(f'<li><a href="#{i}">{n}</a></li>' for i, n in c["sections"])
        ch += (f'<li class="ch"><a href="#{c["anchor"]}"><span class="num">{c["num"]}</span>'
               f'{html.escape(c["title"])}</a><ol>{subs}</ol></li>')
    return f'<div class="toc"><h1 id="contents">Contents</h1><ol>{fm}{ch}</ol></div>'


def _chapter(c):
    opener = f'''
<div class="opener" id="{c["anchor"]}">
  <div class="num-label">Chapter</div>
  <div class="num">{c["num"]}</div>
  <h1>{html.escape(c["title"])}</h1>
  <div class="question">{html.escape(c["question"])}</div>
</div>'''
    return (f'<div class="chapter" data-num="{c["num"]}" data-title="{html.escape(c["title"])}">'
            f'{opener}<div class="body">{c["html"]}</div></div>')


def build_pdf(parts, chapters, prod_dir, out_dir, name="Frontend-Dragon", html_only=False):
    os.makedirs(out_dir, exist_ok=True)
    fm = '<div class="frontmatter">' + "".join(f"<section>{p['html']}</section>" for p in parts) + "</div>"
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{BOOK["title"]}</title>
<link rel="stylesheet" href="{os.path.join(prod_dir, "book.css")}"></head><body>
{_cover()}
{_colophon()}
{_toc(parts, chapters)}
{fm}
{"".join(_chapter(c) for c in chapters)}
</body></html>'''
    html_path = os.path.join(out_dir, f"{name}.html")
    open(html_path, "w", encoding="utf-8").write(doc)
    print("wrote", html_path)
    if html_only:
        return html_path
    from weasyprint import HTML
    pdf_path = os.path.join(out_dir, f"{name}.pdf")
    HTML(html_path, base_url=prod_dir).write_pdf(pdf_path)
    print("wrote", pdf_path)
    return pdf_path
