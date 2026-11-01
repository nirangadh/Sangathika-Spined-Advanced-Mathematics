#!/usr/bin/env python3
# සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
"""Build helper. The site needs no build step to be served; this script keeps the
generated parts in step with tools/leaves.json, and its output is committed.

Writes: the tree illustration and the QR code into index.html; the thirteen leaf
pages; the head region (between <!-- sam:head --> and <!-- /sam:head -->) of every
page; sitemap.xml; robots.txt (once); 404.html; assets/icon.svg; and, when Playwright
is installed, the social cards and the touch icon (rendered only when their source
changes). Run from the repository root: python3 tools/build.py
Build-time tools only (never loaded by a page): segno for the QR code, Playwright
with Chromium for rasterising cards. See NOTICES.md.
"""
import datetime, hashlib, html, json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "leaves.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
ORIGIN = SITE["origin"]
LICENCE_URL = SITE["licence"]
PERSON_ID = ORIGIN + "/about/#author"
WEBSITE_ID = ORIGIN + "/#website"
LEAVES = {l["slug"]: l for l in DATA["leaves"]}
HATCHED = {"hatched", "building", "complete"}

HEADER = """<!-- සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna.
     Text and illustrations in this file: CC BY-SA 4.0 (see LICENSE-CONTENT).
     JavaScript and CSS in this file: MIT (see LICENSE).
     The name සංගතික, the wordmark and the tree mark are reserved (see NOTICES.md). -->"""
SVG_META = "<metadata>සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. CC BY-SA 4.0.</metadata>"
ATTRIBUTION = "සංගතික · Sangathika by Niranga Dharmaratna, CC BY-SA 4.0, https://www.sangathika.com/"

# ----------------------------------------------------------------- helpers

def esc(s):
    return html.escape(s, quote=True)

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

def lastmod(path):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(path)], cwd=ROOT,
                             capture_output=True, text=True, timeout=20).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    return datetime.date.today().isoformat()

def set_region(text, start, end, content):
    a, b = text.index(start), text.index(end)
    return text[:a + len(start)] + "\n" + content + "\n" + text[b:]

def is_indexed(leaf):
    return leaf["status"] in HATCHED

def term_slug(term):
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")

# ----------------------------------------------------------------- page records

def pages():
    """Every page that carries a generated head: path, URL, title, description, JSON-LD, flags."""
    recs = []
    person = {"@type": "Person", "@id": PERSON_ID, "name": SITE["author"]["name"],
              "url": SITE["author"]["url"], "sameAs": SITE["author"]["same_as"]}
    recs.append({
        "path": ROOT / "index.html", "url": ORIGIN + "/", "og_type": "website", "card": "tree",
        "title": "Sangathika: interactive, visual mathematics, free and open",
        "og_title": "Sangathika: interactive, visual mathematics, free and open",
        "description": "Free, open mathematics lessons for computing students. Drag, predict, then read: one idea per page, built up leaf by leaf.",
        "card_alt": "The Sangathika tree, with thirteen labelled leaves",
        "noindex": False,
        "jsonld": {"@context": "https://schema.org", "@graph": [
            {"@type": "WebSite", "@id": WEBSITE_ID, "name": SITE["name"], "alternateName": SITE["alternate_names"],
             "url": ORIGIN + "/", "inLanguage": SITE["language"], "publisher": {"@id": PERSON_ID},
             "license": LICENCE_URL},
            person]},
    })
    recs.append({
        "path": ROOT / "about" / "index.html", "url": ORIGIN + "/about/", "og_type": "profile", "card": "tree",
        "title": "About Sangathika and its author | Sangathika",
        "og_title": "About Sangathika and its author",
        "description": "Who writes Sangathika, how each lesson page is built, how to reuse it under CC BY-SA 4.0, and how to propose a page.",
        "card_alt": "The Sangathika tree, with thirteen labelled leaves",
        "noindex": False,
        "jsonld": {"@context": "https://schema.org", "@graph": [
            {"@type": "ProfilePage", "url": ORIGIN + "/about/", "name": "About Sangathika and its author",
             "inLanguage": SITE["language"], "isPartOf": {"@id": WEBSITE_ID}, "mainEntity": {"@id": PERSON_ID},
             "license": LICENCE_URL},
            person,
            breadcrumb([("Sangathika", ORIGIN + "/"), ("About", ORIGIN + "/about/")])]},
    })
    for slug in DATA["order"]:
        L = LEAVES[slug]
        url = f"{ORIGIN}/{slug}/"
        target = len(L.get("pages", [])) or L.get("target", 0)
        if is_indexed(L):
            title = f"{L['seo_name']}: {target} interactive lessons | Sangathika"
            desc = f"{strip_tags(L['brief'])} {target} lessons, each one idea: drag, predict, then read why."
            graph = [course(L, url), breadcrumb([("Sangathika", ORIGIN + "/"), (L["seo_name"], url)])]
            if L.get("glossary"):
                graph.append(termset(L, url))
        else:
            title = f"{L['seo_name']} | Sangathika"
            desc = f"{strip_tags(L['brief'])} The lessons for this leaf are being prepared."
            graph = [breadcrumb([("Sangathika", ORIGIN + "/"), (L["seo_name"], url)])]
        recs.append({
            "path": ROOT / slug / "index.html", "url": url, "og_type": "website", "card": slug,
            "title": title, "og_title": title.replace(" | Sangathika", ""), "description": desc,
            "card_alt": f"The {L['seo_name']} leaf of the Sangathika tree",
            "noindex": not is_indexed(L), "leaf": slug,
            "jsonld": {"@context": "https://schema.org", "@graph": graph},
        })
    return recs

def breadcrumb(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def course(L, url):
    c = {"@type": "Course", "name": L["seo_name"], "description": strip_tags(L["sentence"]), "url": url,
         "inLanguage": SITE["language"], "educationalLevel": "first-year undergraduate",
         "isAccessibleForFree": True, "license": LICENCE_URL, "author": {"@id": PERSON_ID}}
    built = [f"{url}{p['slug']}/" for p in L.get("pages", []) if p.get("status") == "built"]
    if built:
        c["hasPart"] = [{"@type": "LearningResource", "url": u} for u in built]
    return c

def termset(L, url):
    return {"@type": "DefinedTermSet", "name": f"{L['seo_name']} glossary", "url": url + "#glossary",
            "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["term"], "description": strip_tags(t["def"]),
                                "url": f"{url}#term-{term_slug(t['term'])}"} for t in L["glossary"]]}

def head_region(rec, prefix):
    """The generated head. prefix is the relative path from the page to the site root."""
    card_url = f"{ORIGIN}/assets/cards/{rec['card']}.png"
    lines = [
        f"<title>{esc(rec['title'])}</title>",
        f'<meta name="description" content="{esc(rec["description"])}">',
    ]
    if rec["noindex"]:
        lines.append('<meta name="robots" content="noindex, follow">')
    lines += [
        f'<link rel="canonical" href="{rec["url"]}">',
        f'<meta property="og:type" content="{rec["og_type"]}">',
        '<meta property="og:site_name" content="Sangathika">',
        '<meta property="og:locale" content="en_GB">',
        f'<meta property="og:title" content="{esc(rec["og_title"])}">',
        f'<meta property="og:description" content="{esc(rec["description"])}">',
        f'<meta property="og:url" content="{rec["url"]}">',
        f'<meta property="og:image" content="{card_url}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{esc(rec["card_alt"])}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<script type="application/ld+json">' + json.dumps(rec["jsonld"], ensure_ascii=False, separators=(",", ":")) + "</script>",
    ]
    return "\n".join(lines)

def expected_heads():
    """Used by tools/check.py: path -> generated head text."""
    out = {}
    for rec in pages():
        depth = len(rec["path"].relative_to(ROOT).parts) - 1
        out[rec["path"]] = head_region(rec, "../" * depth)
    return out

# ----------------------------------------------------------------- QR code and tree

def qr_svg():
    import segno
    q = segno.make(ORIGIN + "/", error="m")
    svg = q.svg_inline(scale=1, border=2, dark="#33363d", light="#fff7e9", omitsize=True)
    svg = svg.replace("<svg ", '<svg role="img" aria-labelledby="qr-t" ', 1)
    i = svg.index(">") + 1
    svg = svg[:i] + '<title id="qr-t">QR code for www.sangathika.com</title>' + SVG_META + svg[i:]
    return '<div class="tile">' + svg + "</div>"

def inline_tree_and_qr():
    idx = ROOT / "index.html"
    text = idx.read_text(encoding="utf-8")
    svg = re.sub(r"^\s*<\?xml[^>]*>\s*", "", (ROOT / "assets" / "tree.svg").read_text(encoding="utf-8"))
    text = set_region(text, "<!-- TREE -->", "<!-- /TREE -->", svg.rstrip())
    try:
        text = set_region(text, "<!-- QR -->", "<!-- /QR -->", qr_svg())
    except ImportError:
        print("segno not installed: QR code left as it was")
    idx.write_text(text, encoding="utf-8")

# ----------------------------------------------------------------- leaf pages

CAST_SYM = {"triangle": "ic-tri", "towns": "ic-towns", "dial": "ic-dial", "fifteen": "ic-fifteen"}
SYMBOLS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <symbol id="ic-tri" viewBox="0 0 24 24"><path d="M4 20 L4 8 L20 20 Z" fill="var(--crimson-tint)" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round"/><path d="M4 16 h3 v4" fill="none" stroke="var(--ink)" stroke-width="1"/></symbol>
  <symbol id="ic-towns" viewBox="0 0 24 24"><path d="M2 20 h20" stroke="var(--ink)" stroke-width="1.5"/><path d="M3 20 v-6 l3-3 3 3 v6 Z" fill="var(--steel-tint)" stroke="var(--ink)" stroke-width="1.3" stroke-linejoin="round"/><path d="M15 20 v-6 l3-3 3 3 v6 Z" fill="var(--crimson-tint)" stroke="var(--ink)" stroke-width="1.3" stroke-linejoin="round"/><path d="M9 17 h6" stroke="var(--bark)" stroke-width="1.5" stroke-dasharray="2 1.5"/></symbol>
  <symbol id="ic-dial" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="var(--surface)" stroke="var(--ink)" stroke-width="1.5"/><path d="M12 3.5v2 M20.5 12h-2 M12 20.5v-2 M3.5 12h2" stroke="var(--ink)" stroke-width="1.3"/><path d="M12 12 L17 8" stroke="var(--crimson)" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="12" r="1.3" fill="var(--ink)"/></symbol>
  <symbol id="ic-fifteen" viewBox="0 0 24 24"><g fill="var(--steel)"><circle cx="5" cy="5" r="1.6"/><circle cx="12" cy="5" r="1.6"/><circle cx="19" cy="5" r="1.6"/><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/><circle cx="5" cy="19" r="1.6"/><circle cx="12" cy="19" r="1.6"/><circle cx="19" cy="19" r="1.6"/></g><path d="M2 21 L22 7" stroke="var(--crimson)" stroke-width="1.5" fill="none"/></symbol>
</defs></svg>"""

THEME_JS = """<script>
(function(){var b=document.getElementById('themeBtn'),h=document.documentElement;function cur(){var t=h.getAttribute('data-theme');if(t)return t;return window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}function paint(){var d=cur()==='dark';b.textContent=d?'Light':'Dark';b.setAttribute('aria-pressed',d?'true':'false')}b.addEventListener('click',function(){var n=cur()==='dark'?'light':'dark';h.setAttribute('data-theme',n);try{localStorage.setItem('sam-theme',n)}catch(e){}paint()});paint();})();
</script>"""
THEME_PRE = "<script>try{var t=localStorage.getItem('sam-theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>"

def leaf_svg(leaf, size=240, title=True):
    spots = [(118, 96), (82, 128), (154, 134), (118, 170)]
    icons = "".join(f'<use href="#{CAST_SYM[c]}" x="{spots[i][0]-11}" y="{spots[i][1]-11}" width="22" height="22"/>'
                    for i, c in enumerate(leaf["cast"][:4]))
    t = (f'<title id="lf-t">The {esc(leaf["seo_name"])} leaf, with the cast objects it uses drawn on its veins</title>'
         if title else "")
    return f"""<svg viewBox="0 0 240 240" role="img" aria-labelledby="lf-t">{t}
{SVG_META}
<path d="M120,226 C40,180 24,100 120,16 C216,100 200,180 120,226 Z" fill="var(--moss-tint)" stroke="var(--ink)" stroke-width="2.4"/>
<path d="M120,226 L120,16" fill="none" stroke="var(--eig)" stroke-width="2"/>
<g fill="none" stroke="var(--eig)" stroke-width="1.2"><path d="M120,60 C100,70 84,84 70,100 M120,60 C140,70 156,84 170,100 M120,96 C98,108 84,124 72,142 M120,96 C142,108 156,124 168,142 M120,134 C104,146 94,158 86,172 M120,134 C136,146 146,158 154,172 M120,170 C110,180 104,190 100,198 M120,170 C130,180 136,190 140,198"/></g>
<path d="M120,226 C118,236 116,240 112,240" fill="none" stroke="var(--bark)" stroke-width="3" stroke-linecap="round"/>
{icons}
</svg>"""

def midrib(leaf):
    items = []
    plist = leaf.get("pages") or [{"number": i, "title": "planned lesson", "status": "planned"}
                                  for i in range(1, leaf.get("target", 16) + 1)]
    for p in plist:
        n = f'{p["number"]:02d}'
        label = esc(f'Page {p["number"]}: {p["title"]}')
        if p.get("status") == "built":
            items.append(f'<li class="built"><a href="{p["slug"]}/" title="{label}" aria-label="{label}">{n}</a></li>')
        elif p.get("status") == "porting":
            items.append(f'<li class="built"><span title="{label}, coming online" aria-label="{label}, coming online">{n}</span></li>')
        else:
            items.append(f'<li><span title="{label}" aria-label="{label}">{n}</span></li>')
    return '<ol class="midrib" aria-label="Lessons in this leaf">' + "".join(items) + "</ol>"

def chips(levels):
    return " ".join(f'<span class="chip {l.lower()}">{l}</span>' for l in levels)

def pages_table(leaf):
    rows = []
    for p in leaf["pages"]:
        title, built = esc(p["title"]), p.get("status") == "built"
        if built:
            notes = f'<a href="{p["slug"]}/">{title}</a>'
            demos = "".join(f'<a href="{p["slug"]}/#plate-{p["number"]}-{d["k"]}">{esc(d["name"])}</a>' for d in p.get("demos", []))
        else:
            notes = '<span class="chip built">coming online</span>' if p.get("status") == "porting" else '<span class="chip">coming</span>'
            demos = "".join(f'<span class="coming">{esc(d["name"])}</span>' for d in p.get("demos", []))
        cls = "" if built else ' class="coming"'
        rows.append(f'<tr{cls}><td class="n" data-l="Page">{p["number"]:02d}</td><td class="t" data-l="Title">{title}</td>'
                    f'<td data-l="Brief">{p["brief"]}</td><td data-l="Lesson">{notes}</td><td class="demos" data-l="Demos">{demos}</td>'
                    f'<td data-l="Challenges">{chips(p.get("levels", []))}</td><td data-l="Hands forward">{esc(p.get("forward", ""))}</td></tr>')
    return ('<table class="pages"><thead><tr><th>Page</th><th>Title</th><th>Brief</th><th>Lesson</th><th>Demos</th>'
            '<th>Challenges</th><th>Hands forward</th></tr></thead><tbody>\n' + "\n".join(rows) + "\n</tbody></table>")

def branches_table(leaf):
    if not leaf.get("branches"):
        return ""
    rows = "\n".join(f'<tr class="coming"><td class="t" data-l="Branch">{esc(b["title"])}</td><td data-l="Brief">{b["brief"]}</td>'
                     f'<td data-l="Needs">{esc(b["needs"])}</td><td data-l="Lesson"><span class="chip">coming</span></td></tr>'
                     for b in leaf["branches"])
    return f"""<section id="branches">
<h2>Applications that hang from this leaf</h2>
<p>Each application hangs from the lessons it needs. It is built once those lessons exist.</p>
<table class="pages"><thead><tr><th>Branch</th><th>Brief</th><th>Needs</th><th>Lesson</th></tr></thead><tbody>
{rows}
</tbody></table>
</section>"""

def glossary(leaf):
    terms = leaf.get("glossary", [])
    if not terms:
        return '<p class="small">Every new word from this leaf appears here, with one sentence and the lesson that introduces it.</p>'
    return '<dl class="glossary">' + "".join(
        f'<dt id="term-{term_slug(t["term"])}">{esc(t["term"])} <span class="small mono">page {t["page"]:02d}</span></dt><dd>{t["def"]}</dd>'
        for t in terms) + "</dl>"

def use_in_course(leaf):
    if not is_indexed(leaf):
        return ""
    return f"""<section id="use">
<h2>Use this in your course</h2>
<p>Link to any lesson, or to one demo on it: every demo has its own link, shown in the Demos column. You may also copy and adapt these lessons under the CC BY-SA 4.0 licence. Please credit them like this:</p>
<pre><code>{esc(ATTRIBUTION)}</code></pre>
<p class="small">More about reuse on the <a href="../about/#reuse">about page</a>.</p>
</section>"""

def leaf_page(leaf):
    plist = leaf.get("pages", [])
    built = sum(1 for p in plist if p.get("status") in ("built", "porting"))
    total = len(plist) or leaf.get("target", 16)
    prereq = ", ".join(f'<a href="../{s}/">{esc(LEAVES[s]["seo_name"])}</a>' for s in leaf.get("prereq", [])) \
        or "grid coordinates, arithmetic and Pythagoras"
    feeds = ", ".join(f'<a href="../{s}/">{esc(LEAVES[s]["seo_name"])}</a>' for s in leaf.get("feeds", []) if s in LEAVES) or "later leaves"
    cast_names = {"triangle": "the 3-4-5 triangle", "towns": "the two towns", "dial": "the dial", "fifteen": "the fifteen"}
    cast_line = ", ".join(cast_names[c] for c in leaf["cast"]) or "none"
    if plist:
        body = pages_table(leaf)
    else:
        body = ('<div class="callout"><p><b>This leaf is planned.</b> Its lessons are being designed now, and each one appears here when it is built. '
                f'The strip above shows its planned length.</p><p class="small" style="margin:0">{esc(leaf.get("why", ""))}</p></div>')
    teacher = leaf.get("teacher") or "The sequencing for this leaf is published with its first lessons."
    status_chip = leaf["status"] if leaf["status"] in HATCHED else "planned"
    return f"""<!doctype html>
<html lang="en-GB">
{HEADER}
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- sam:head -->
<!-- /sam:head -->
<link rel="preload" href="../assets/fonts/opensans/OpenSans[wdth,wght].ttf" as="font" type="font/ttf" crossorigin>
<link rel="preload" href="../assets/fonts/stixtwotext/STIXTwoText[wght].ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="../assets/sam.css">
<link rel="icon" href="../assets/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/icon-180.png">
{THEME_PRE}
</head>
<body>
{SYMBOLS}
<div class="wrap">
<header class="bar">
  <a class="mark" href="../"><span class="si" lang="si">සංගතික</span><span class="latin">Sangathika</span></a>
  <nav aria-label="Site"><a href="../#leaves">All leaves</a><a href="#lessons">Lessons</a><a href="#glossary">Glossary</a><a href="../about/">About</a><button class="theme" type="button" id="themeBtn" aria-pressed="false">Dark</button></nav>
</header>

<section class="leaf-head">
  <div>
    <p class="eyebrow"><b>SAM</b> · {esc(leaf["group"])} · leaf</p>
    <h1>{esc(leaf["name"])}</h1>
    <p class="idea">{leaf["sentence"]}</p>
    <p class="prereq">Before this leaf: {prereq}.<br>This leaf feeds: {feeds}.<br>Objects you will meet again: {cast_line}.</p>
    <p class="meta"><span class="chip {status_chip}">{status_chip}</span> <span class="mono small progress">{built} of {total} lessons built</span></p>
  </div>
  <figure>{leaf_svg(leaf)}</figure>
</section>

{midrib(leaf)}

<section id="lessons">
<h2>Lessons, notes and demos</h2>
<p>One row per lesson, in the order the leaf builds up. Each lesson holds its notes, its demos and its challenges on one page. A demo link opens the lesson at that demo.</p>
{body}
</section>

{branches_table(leaf)}

{use_in_course(leaf)}

<section id="glossary">
<h2>Glossary</h2>
{glossary(leaf)}
</section>

<section id="teacher">
<h2>For the teacher</h2>
<details class="notes"><summary>Sequencing and rationale</summary><p>{teacher}</p></details>
</section>

<footer class="site">
  <p>© 2026 Niranga Dharmaratna. Text and illustrations CC BY-SA 4.0; code MIT. <span class="si" lang="si">සංගතික</span> and its marks are reserved. <a href="../about/">About Sangathika</a>.</p>
</footer>
</div>
{THEME_JS}
</body>
</html>
"""

# ----------------------------------------------------------------- 404, sitemap, robots, icon

def page_404():
    links = "".join(f'<li><a href="/{s}/">{esc(LEAVES[s]["seo_name"])}</a></li>' for s in DATA["order"])
    return f"""<!doctype html>
<html lang="en-GB">
{HEADER}
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found | Sangathika</title>
<link rel="stylesheet" href="/assets/sam.css">
<link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
{THEME_PRE}
</head>
<body>
<div class="wrap">
<header class="bar"><a class="mark" href="/"><span class="si" lang="si">සංගතික</span><span class="latin">Sangathika</span></a><nav aria-label="Site"><a href="/about/">About</a><button class="theme" type="button" id="themeBtn" aria-pressed="false">Dark</button></nav></header>
<section class="hero">
<p class="eyebrow"><b>SAM</b> · page not found</p>
<h1>This page is not on the tree</h1>
<p class="lede">The address may be mistyped, or the lesson may not be built yet. Start again from <a href="/">the tree</a>, or choose a leaf.</p>
<ul>{links}</ul>
</section>
<footer class="site"><p>© 2026 Niranga Dharmaratna. Text and illustrations CC BY-SA 4.0; code MIT.</p></footer>
</div>
{THEME_JS}
</body>
</html>
"""

def sitemap(recs):
    urls = []
    for r in recs:
        if r["noindex"]:
            continue
        urls.append(f"<url><loc>{r['url']}</loc><lastmod>{lastmod(r['path'])}</lastmod></url>")
    for L in LEAVES.values():
        for p in L.get("pages", []):
            if p.get("status") == "built":
                path = ROOT / L["slug"] / p["slug"] / "index.html"
                urls.append(f"<url><loc>{ORIGIN}/{L['slug']}/{p['slug']}/</loc><lastmod>{lastmod(path)}</lastmod></url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"

ROBOTS = f"""User-agent: *
Disallow: /tools/
Disallow: /*.md$

Sitemap: {ORIGIN}/sitemap.xml
"""

ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-labelledby="ic-t"><title id="ic-t">Sangathika</title>{SVG_META}
<rect width="64" height="64" rx="14" fill="#fff7e9"/>
<path d="M32,58 C10,46 6,26 32,6 C58,26 54,46 32,58 Z" fill="#dfe6cf" stroke="#33363d" stroke-width="3" stroke-linejoin="round"/>
<path d="M32,58 L32,8" stroke="#6f8f4a" stroke-width="2.5" fill="none"/>
<path d="M32,22 L22,30 M32,22 L42,30 M32,34 L21,42 M32,34 L43,42" stroke="#6f8f4a" stroke-width="2" fill="none" stroke-linecap="round"/>
<circle cx="32" cy="58" r="3" fill="#b24d7a"/>
</svg>
"""

# ----------------------------------------------------------------- social cards (rasterised, cached by source hash)

def card_html(art, heading, sub):
    css = (ROOT / "assets" / "sam.css").resolve().as_uri()
    return f"""<!doctype html><html lang="en-GB" data-theme="light"><head><meta charset="utf-8"><link rel="stylesheet" href="{css}">
<style>html,body{{margin:0;width:1200px;height:630px;overflow:hidden;background:var(--paper)}}
.sc{{box-sizing:border-box;width:1200px;height:630px;padding:56px 64px;display:grid;grid-template-columns:1fr 470px;gap:40px;align-items:center;border-bottom:14px solid var(--crimson)}}
.sc h1{{font-family:var(--f-display);font-size:68px;line-height:1.08;margin:0 0 22px;color:var(--ink)}}
.sc p{{font-family:var(--f-body);font-size:28px;line-height:1.35;color:var(--muted);margin:0;max-width:none}}
.wm{{position:absolute;z-index:2;left:64px;top:44px;font-size:26px;color:var(--crimson);font-weight:600}}
.wm .latin{{font-family:var(--f-display);color:var(--ink);font-weight:500;margin-left:10px}}
.art svg{{width:100%;height:auto;max-height:520px;display:block}}</style></head>
<body>{SYMBOLS}<div class="wm"><span class="si" lang="si">සංගතික</span><span class="latin">Sangathika</span></div>
<div class="sc"><div><h1>{esc(heading)}</h1><p>{esc(sub)}</p></div><div class="art">{art}</div></div></body></html>"""

def cards(recs):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed: social cards and touch icon not rendered")
        return
    outdir = ROOT / "assets" / "cards"
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_p = outdir / "manifest.json"
    manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {}
    tree = (ROOT / "assets" / "tree.svg").read_text(encoding="utf-8")
    jobs = {"tree": card_html(tree, "Mathematics, one idea at a time", "Free, open, interactive lessons for computing students.")}
    for r in recs:
        if r.get("leaf"):
            L = LEAVES[r["leaf"]]
            jobs[L["slug"]] = card_html(leaf_svg(L), L["seo_name"], strip_tags(L["brief"]))
    jobs["_icon180"] = ICON
    todo = {k: v for k, v in jobs.items() if manifest.get(k) != hashlib.sha256(v.encode()).hexdigest()
            or not (ROOT / ("assets/icon-180.png" if k == "_icon180" else f"assets/cards/{k}.png")).exists()}
    if not todo:
        return
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for k, h in todo.items():
            if k == "_icon180":
                pg = b.new_page(viewport={"width": 180, "height": 180})
                pg.set_content(f'<html><body style="margin:0">{h.replace("<svg ", "<svg width=180 height=180 ", 1)}</body></html>')
                pg.screenshot(path=str(ROOT / "assets" / "icon-180.png"))
            else:
                pg = b.new_page(viewport={"width": 1200, "height": 630})
                tmp = outdir / f".{k}.html"
                tmp.write_text(h, encoding="utf-8")
                pg.goto(tmp.as_uri()); pg.wait_for_timeout(250)
                pg.screenshot(path=str(outdir / f"{k}.png"))
                tmp.unlink()
            pg.close()
            manifest[k] = hashlib.sha256(h.encode()).hexdigest()
            print("rendered", k)
        b.close()
    manifest_p.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")

# ----------------------------------------------------------------- main

def main():
    inline_tree_and_qr()
    for slug in DATA["order"]:
        d = ROOT / slug
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(leaf_page(LEAVES[slug]), encoding="utf-8")
    recs = pages()
    for path, head in expected_heads().items():
        t = path.read_text(encoding="utf-8")
        path.write_text(set_region(t, "<!-- sam:head -->", "<!-- /sam:head -->", head), encoding="utf-8")
    (ROOT / "404.html").write_text(page_404(), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(recs), encoding="utf-8")
    if not (ROOT / "robots.txt").exists():
        (ROOT / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (ROOT / "assets" / "icon.svg").write_text(ICON, encoding="utf-8")
    cards(recs)
    print("build done:", len(recs), "pages with generated heads")

if __name__ == "__main__":
    main()
