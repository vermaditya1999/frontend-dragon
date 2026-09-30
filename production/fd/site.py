"""Static-site target: one HTML page per front-matter part and per chapter.

Shell behaviour (all in the inline script below, no dependencies):
  - sidebar is a drawer: hidden on desktop until the reader hovers the left edge or the
    menu button; a pin keeps it open (remembered in localStorage 'fd-nav')
  - the "on this page" outline fades out after a few seconds of reading and comes back
    on scroll or hover
  - on phones the top bar hides on scroll-down and returns on scroll-up
  - theme toggle lives in the fixed top-right control on every width
"""
import html, os, shutil
from .convert import BOOK

ICON_MENU = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none"/></svg>'
ICON_THEME = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="10" cy="10" r="6.5" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M10 3.5v13A6.5 6.5 0 0 0 10 3.5z" fill="currentColor"/></svg>'
ICON_PIN = '<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M12.5 3l4.5 4.5-2 2-.7-.7-3 3 .4 3.2-1.5 1.5-3.4-3.4L3.5 16.5 2.8 15.8 6.1 12.5 2.7 9.1 4.2 7.6l3.2.4 3-3-.7-.7z" fill="currentColor"/></svg>'

NAV_JS = r"""
(function () {
  var root = document.documentElement, body;
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  // theme: applied before first paint (script is in <head>)
  var t = load('fd-theme'); if (t === 'dark' || t === 'light') root.setAttribute('data-theme', t);
  function toggleTheme() {
    var cur = root.getAttribute('data-theme');
    var dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    var next = dark ? 'light' : 'dark'; root.setAttribute('data-theme', next); store('fd-theme', next);
  }

  document.addEventListener('DOMContentLoaded', function () {
    body = document.body;
    var q = function (s) { return document.querySelector(s); };
    var nav = q('.sidebar'), edge = q('.nav-edge'), menuBtn = q('[data-nav]'), pinBtn = q('[data-pin]');
    var mqDesktop = matchMedia('(min-width: 861px)');

    Array.prototype.forEach.call(document.querySelectorAll('[data-theme-toggle]'), function (b) {
      b.addEventListener('click', toggleTheme);
    });

    // ---- sidebar drawer ----
    if (load('fd-nav') === 'pinned' && mqDesktop.matches) body.classList.add('nav-pinned');
    var hoverTimer;
    function open() { clearTimeout(hoverTimer); body.classList.add('nav-open'); }
    function close() { if (!body.classList.contains('nav-pinned')) body.classList.remove('nav-open'); }
    function closeSoon() { clearTimeout(hoverTimer); hoverTimer = setTimeout(close, 250); }
    if (edge) { edge.addEventListener('mouseenter', open); edge.addEventListener('mouseleave', closeSoon); }
    if (nav) { nav.addEventListener('mouseenter', open); nav.addEventListener('mouseleave', closeSoon); }
    if (menuBtn) {
      menuBtn.addEventListener('mouseenter', function () { if (mqDesktop.matches) open(); });
      menuBtn.addEventListener('mouseleave', function () { if (mqDesktop.matches) closeSoon(); });
      menuBtn.addEventListener('click', function () {
        if (body.classList.contains('nav-pinned')) { body.classList.remove('nav-pinned', 'nav-open'); store('fd-nav', ''); return; }
        body.classList.toggle('nav-open');
      });
    }
    if (pinBtn) pinBtn.addEventListener('click', function () {
      var pinned = body.classList.toggle('nav-pinned');
      if (pinned) body.classList.add('nav-open'); else body.classList.remove('nav-open');
      store('fd-nav', pinned ? 'pinned' : '');
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { body.classList.remove('nav-open'); } });
    // tapping the dimmed page closes the drawer on phones
    var scrim = q('.scrim'); if (scrim) scrim.addEventListener('click', function () { body.classList.remove('nav-open'); });

    // ---- outline: fade after idle, return on scroll / hover ----
    var onpage = q('.onpage'), idleTimer;
    function outlineShow() { if (!onpage) return; onpage.classList.remove('idle'); clearTimeout(idleTimer); idleTimer = setTimeout(function () { onpage.classList.add('idle'); }, 4000); }
    if (onpage) { outlineShow(); onpage.addEventListener('mouseenter', function () { clearTimeout(idleTimer); onpage.classList.remove('idle'); }); onpage.addEventListener('mouseleave', outlineShow); }

    // ---- mobile top bar: hide on scroll down, show on scroll up ----
    var lastY = window.scrollY, topbar = q('.topbar');
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      if (topbar) {
        if (y > lastY + 6 && y > 80) body.classList.add('bar-hidden');
        else if (y < lastY - 6 || y < 40) body.classList.remove('bar-hidden');
      }
      lastY = y;
      outlineShow();
    }, { passive: true });

    // ---- outline: highlight current section ----
    var links = Array.prototype.slice.call(document.querySelectorAll('.onpage a'));
    if (links.length && 'IntersectionObserver' in window) {
      var map = {};
      links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { links.forEach(function (a) { a.classList.remove('active'); }); var a = map[en.target.id]; if (a) a.classList.add('active'); }
        });
      }, { rootMargin: '0px 0px -70% 0px' });
      Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
    }
  });
})();
"""


def _sidebar(parts, chapters, current):
    items = [f'<li class="{"active" if current == "index" else ""}"><a href="index.html">Contents</a></li>',
             '<li class="group">Front matter</li>']
    for p in parts:
        items.append(f'<li class="{"active" if current == p["id"] else ""}"><a href="{p["id"]}.html">{p["title"]}</a></li>')
    items.append('<li class="group">Chapters</li>')
    for c in chapters:
        items.append(f'<li class="{"active" if current == c["slug"] else ""}"><a href="{c["slug"]}.html">'
                     f'<span class="num">{c["num"]}</span>{html.escape(c["title"])}</a></li>')
    return (f'<nav class="sidebar" aria-label="Book contents">'
            f'<div class="brand"><a href="index.html"><img class="thumb" src="assets/cover-512.jpg" alt="">'
            f'<span><span class="t">{BOOK["title"]}</span><span class="sub">{BOOK["subtitle"]}</span></span></a>'
            f'<button class="pin" data-pin aria-label="Keep contents open" title="Keep open">{ICON_PIN}</button></div>'
            f'<ul>{"".join(items)}</ul></nav>')


def _page(title, body_html, parts, chapters, current, onpage="", prev=None, nxt=None):
    pager = ""
    if prev or nxt:
        p = f'<a class="prev" href="{prev[0]}"><span>Previous</span>{prev[1]}</a>' if prev else "<span></span>"
        n = f'<a class="next" href="{nxt[0]}"><span>Next</span>{nxt[1]}</a>' if nxt else "<span></span>"
        pager = f'<div class="pager">{p}{n}</div>'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · {BOOK["title"]}</title>
<link rel="stylesheet" href="site.css">
<script>{NAV_JS}</script>
</head>
<body class="page-{current}">
<div class="nav-edge" aria-hidden="true"></div>
<div class="scrim" aria-hidden="true"></div>
<header class="topbar">
  <button class="ctl" data-nav aria-label="Contents">{ICON_MENU}</button>
  <a class="topbrand" href="index.html">{BOOK["title"]}</a>
  <button class="ctl" data-theme-toggle aria-label="Toggle dark mode">{ICON_THEME}</button>
</header>
{_sidebar(parts, chapters, current)}
<main class="reading">
{body_html}
{pager}
</main>
<aside class="onpage" aria-label="On this page">{onpage}</aside>
</body>
</html>'''


def _onpage(sections):
    if not sections:
        return ""
    lis = "".join(f'<li><a href="#{i}">{html.escape(n)}</a></li>' for i, n in sections)
    return f'<div class="onpage-inner"><div class="label">On this page</div><ul>{lis}</ul></div>'


def build_site(parts, chapters, prod_dir, out_dir):
    site = os.path.join(out_dir, "site")
    os.makedirs(site, exist_ok=True)
    shutil.copy(os.path.join(prod_dir, "site.css"), os.path.join(site, "site.css"))
    for sub in ("assets", os.path.join("fonts", "lib")):
        src = os.path.join(prod_dir, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(site, "assets" if sub == "assets" else "fonts"), dirs_exist_ok=True)

    order = [(p["id"] + ".html", p["title"]) for p in parts] + \
            [(c["slug"] + ".html", f'{c["num"]}. {c["title"]}') for c in chapters]

    def neighbours(i):
        return (order[i - 1] if i > 0 else None, order[i + 1] if i + 1 < len(order) else None)

    # ---- index: centred cover, then a simple contents list ----
    fm_list = "".join(f'<li><a href="{p["id"]}.html">{p["title"]}</a></li>' for p in parts)
    ch_list = "".join(
        f'<li class="ch"><a href="{c["slug"]}.html"><span class="num">{c["num"]}</span>'
        f'<span class="t">{html.escape(c["title"])}</span><span class="q">{html.escape(c["question"])}</span></a></li>'
        for c in chapters)
    first = (parts[0]["id"] + ".html") if parts else "#"
    index_body = f'''
<div class="cover">
  <img class="cover-art" src="assets/cover.jpg" alt="Frontend Dragon book cover">
  <div class="series">{BOOK["edition"]}</div>
  <p class="tagline">{BOOK["tagline"]}</p>
  <a class="start" href="{first}">Start reading</a>
</div>
<div class="contents">
  <h2>Contents</h2>
  <ul class="fm">{fm_list}</ul>
  <ul class="chapters">{ch_list}</ul>
</div>'''
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(
        _page("Contents", index_body, parts, chapters, "index"))

    for i, p in enumerate(parts):
        prev, nxt = neighbours(i)
        body = f'<article class="frontmatter">{p["html"]}</article>'
        open(os.path.join(site, p["id"] + ".html"), "w", encoding="utf-8").write(
            _page(p["title"], body, parts, chapters, p["id"], "", prev, nxt))

    for j, c in enumerate(chapters):
        prev, nxt = neighbours(len(parts) + j)
        opener = f'''
<header class="opener" id="{c["anchor"]}">
  <div class="num-label">Chapter {c["num"]}</div>
  <h1>{html.escape(c["title"])}</h1>
  <p class="question">{html.escape(c["question"])}</p>
</header>'''
        body = f'<article class="chapter">{opener}<div class="body">{c["html"]}</div></article>'
        open(os.path.join(site, c["slug"] + ".html"), "w", encoding="utf-8").write(
            _page(f'{c["num"]}. {c["title"]}', body, parts, chapters, c["slug"], _onpage(c["sections"]), prev, nxt))

    print("wrote", site, f"({len(parts)} front-matter pages, {len(chapters)} chapters)")
    return site
