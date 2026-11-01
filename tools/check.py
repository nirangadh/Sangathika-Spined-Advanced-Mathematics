#!/usr/bin/env python3
# සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
"""Mechanical part of the check pass. Run from the repository root:
    python3 tools/check.py [--render]
Checks: no em dash; licence header or metadata in every HTML, JS, CSS and SVG file;
relative internal links that resolve, never ending in index.html, never root-absolute
(except 404.html); generated head regions match tools/build.py; one h1; title and
description lengths; canonical URLs; structured data; sitemap; social cards; the public
boundary (no internal references or personal addresses in files or the latest commit).
With --render: no horizontal page scroll at 360 px and 1280 px, and no console errors.
Exit code 1 on any failure.
"""
import hashlib, importlib.util, json, pathlib, re, subprocess, sys, html.parser

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_EXT = {".html", ".css", ".js", ".md", ".svg", ".json", ".py", ".txt", ".xml"}
SKIP_DIRS = {".git", "node_modules", "fonts"}
LEGAL = {"LICENSE-CONTENT", "LICENSE-CC0.txt", "OFL.txt"}  # third-party legal text, left verbatim
fails = []

spec = importlib.util.spec_from_file_location("build", ROOT / "tools" / "build.py")
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)

def files():
    for p in sorted(ROOT.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts): continue
        if p.is_file() and (p.suffix in TEXT_EXT or p.name in {"LICENSE", "CNAME"}) and p.name not in LEGAL:
            yield p

def html_pages():
    return [p for p in files() if p.suffix == ".html"]

def rel(p): return p.relative_to(ROOT).as_posix()

# ------------------------------------------------------------ text rules

def check_emdash():
    for p in files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if chr(0x2014) in line:
                fails.append(f"em dash: {rel(p)}:{i}")

def check_headers():
    for p in files():
        t = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".html" and "CC BY-SA 4.0 (see LICENSE-CONTENT)" not in t[:1500]:
            fails.append(f"missing HTML licence header: {rel(p)}")
        if p.suffix in {".js", ".css", ".py"} and "MIT licence, see LICENSE" not in t[:600]:
            fails.append(f"missing MIT header: {rel(p)}")
        if p.suffix == ".svg" and "<metadata>" not in t:
            fails.append(f"missing metadata block: {rel(p)}")
        if p.suffix == ".html":
            for m in re.finditer(r"<svg\b[^>]*>(.*?)</svg>", t, flags=re.S):
                if 'role="img"' in m.group(0)[:300] and "<metadata>" not in m.group(1):
                    fails.append(f"illustration without metadata: {rel(p)} at char {m.start()}")

# The public boundary: what must never appear in the public repository.
# Words and word pairs that must not appear, stored as SHA-256 hashes so that this
# public file does not itself publish them. Compared against every lower-case word
# and every adjacent pair of words.
PRIVATE_HASHES = {
    "adec1a9ac09aa8c8c7490002b99835769c84c4660f76c1de4227c9569b6ec185": "private term",
    "478a607d824bb7c7b130d092dd52999f8a4c4cb6291e90ebc30d00c9e68b0990": "private term",
}

DENY = [
    (r"\bclaude/", "private project path"),
    (r"claude\.ai/(code|chat|project)", "private Claude link"),
    (r"\b(hatch|build|page-build|leaf-hatch) thread", "internal workflow term"),
    (r"merged by hand|work lands on", "internal workflow description"),
    (r"_github-pages-challenge", "domain verification detail"),
    (r"[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook)\.com", "personal email address"),
]

def hashed_hit(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    for w in words + [f"{x} {y}" for x, y in zip(words, words[1:])]:
        why = PRIVATE_HASHES.get(hashlib.sha256(w.encode()).hexdigest())
        if why:
            return why
    return None

def check_boundary():
    for p in files():
        if p == ROOT / "tools" / "check.py": continue
        t = p.read_text(encoding="utf-8", errors="replace")
        for pat, why in DENY:
            for m in re.finditer(pat, t, flags=re.I):
                line = t.count("\n", 0, m.start()) + 1
                fails.append(f"public boundary ({why}): {rel(p)}:{line}")
        for i, line in enumerate(t.splitlines(), 1):
            if hashed_hit(line):
                fails.append(f"public boundary ({hashed_hit(line)}): {rel(p)}:{i}")
    try:
        msg = subprocess.run(["git", "log", "-1", "--format=%an <%ae>%n%B"], cwd=ROOT, capture_output=True, text=True).stdout
        for pat, why in DENY:
            if re.search(pat, msg, flags=re.I):
                fails.append(f"public boundary ({why}): latest commit")
        if hashed_hit(msg):
            fails.append(f"public boundary ({hashed_hit(msg)}): latest commit")
    except Exception:
        pass

# ------------------------------------------------------------ links

class Parse(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.refs = []; self.h1 = 0
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "h1": self.h1 += 1
        if tag == "link" and d.get("rel") in ("canonical",): return
        if tag == "meta": return
        for k in ("href", "src"):
            v = d.get(k)
            if v: self.refs.append(v)

def check_links():
    for p in html_pages():
        ps = Parse(); ps.feed(p.read_text(encoding="utf-8"))
        for ref in ps.refs:
            if ref.startswith(("http:", "https:", "mailto:", "#", "data:")): continue
            target = ref.split("#")[0]
            if not target: continue
            if target.endswith("index.html"):
                fails.append(f"link ends in index.html: {rel(p)} -> {ref}")
            if target.startswith("/") and p.name != "404.html":
                fails.append(f"root-absolute link: {rel(p)} -> {ref}")
            base = ROOT if target.startswith("/") else p.parent
            tp = (base / target.lstrip("/")).resolve()
            if tp.is_dir(): tp = tp / "index.html"
            if not tp.exists():
                fails.append(f"broken link: {rel(p)} -> {ref}")

def check_css_urls():
    for p in files():
        if p.suffix != ".css": continue
        for m in re.finditer(r'url\("?([^")]+)"?\)', p.read_text(encoding="utf-8")):
            u = m.group(1)
            if u.startswith(("data:", "http")): continue
            if not (p.parent / u).exists():
                fails.append(f"missing file referenced in {rel(p)}: {u}")

# ------------------------------------------------------------ search

def check_search():
    heads = build.expected_heads()
    recs = {r["path"]: r for r in build.pages()}
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
    if not sitemap: fails.append("sitemap.xml missing")
    for path, head in heads.items():
        r = recs[path]; t = path.read_text(encoding="utf-8")
        m = re.search(r"<!-- sam:head -->\n(.*?)\n<!-- /sam:head -->", t, flags=re.S)
        if not m or m.group(1) != head:
            fails.append(f"head region out of date (run tools/build.py): {rel(path)}"); continue
        ps = Parse(); ps.feed(t)
        if ps.h1 != 1: fails.append(f"{ps.h1} h1 elements: {rel(path)}")
        if len(r["title"]) > 60: fails.append(f"title over 60 characters ({len(r['title'])}): {rel(path)}")
        if not 70 <= len(r["description"]) <= 160: fails.append(f"description length {len(r['description'])}: {rel(path)}")
        url = build.ORIGIN + "/" + ("" if path.parent == ROOT else rel(path.parent) + "/")
        if r["url"] != url: fails.append(f"canonical {r['url']} != {url}")
        ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', t, flags=re.S)
        try:
            data = json.loads(ld.group(1))
            if not r["noindex"] and build.LICENCE_URL not in json.dumps(data):
                fails.append(f"structured data names no licence: {rel(path)}")
        except Exception as e:
            fails.append(f"structured data does not parse: {rel(path)} ({e})")
        listed = f"<loc>{r['url']}</loc>" in sitemap
        if r["noindex"] and listed: fails.append(f"noindex page in sitemap: {rel(path)}")
        if not r["noindex"] and not listed: fails.append(f"indexed page missing from sitemap: {rel(path)}")
        if not (ROOT / "assets" / "cards" / f"{r['card']}.png").exists():
            fails.append(f"social card missing: assets/cards/{r['card']}.png")
    for L in build.LEAVES.values():
        leaf_html = (ROOT / L["slug"] / "index.html").read_text(encoding="utf-8")
        for p in L.get("pages", []):
            if p.get("status") == "built":
                if f'href="{p["slug"]}/"' not in leaf_html:
                    fails.append(f"orphan: {L['slug']}/{p['slug']}/ not linked from its leaf page")
                if f"<loc>{build.ORIGIN}/{L['slug']}/{p['slug']}/</loc>" not in sitemap:
                    fails.append(f"built page missing from sitemap: {L['slug']}/{p['slug']}/")
    for need in ("CNAME", "robots.txt", "404.html", "assets/icon.svg", "assets/icon-180.png"):
        if not (ROOT / need).exists(): fails.append(f"missing: {need}")
    if (ROOT / "CNAME").exists() and (ROOT / "CNAME").read_text().strip() != "www.sangathika.com":
        fails.append("CNAME does not read www.sangathika.com")

# ------------------------------------------------------------ lessons (page contract)

LIBRARY = ("vec", "add", "sub", "scale", "len", "bearing", "apply", "det", "eigen", "dot", "inverse", "compose")

def check_lessons():
    strips = build.expected_midribs()
    for L in build.LEAVES.values():
        lib = ROOT / L["slug"] / "sam.js"
        defined = set(re.findall(r"^function (\w+)\(", lib.read_text(encoding="utf-8"), flags=re.M)) if lib.exists() else set()
        for pgd in L.get("pages", []):
            if pgd.get("status") != "built": continue
            path = ROOT / L["slug"] / pgd["slug"] / "index.html"
            where = rel(path)
            if not path.exists():
                fails.append(f"built page missing: {where}"); continue
            t = path.read_text(encoding="utf-8")
            for f in ("seo_title", "description", "idea", "teaches", "demos", "levels", "card", "published"):
                if f not in pgd: fails.append(f"leaves.json page {pgd['number']} lacks {f}")
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, flags=re.S)
            if not h1 or pgd["standard_term"].lower() not in re.sub(r"<[^>]+>", "", h1.group(1)).lower():
                fails.append(f"h1 does not contain the standard term '{pgd['standard_term']}': {where}")
            m = re.search(r"<!-- sam:midrib -->\n(.*?)\n<!-- /sam:midrib -->", t, flags=re.S)
            if not m or m.group(1) != strips[path]:
                fails.append(f"lesson strip out of date (run tools/build.py): {where}")
            if pgd["number"] > 1 and 'id="warm-up"' not in t:
                fails.append(f"no warm-up: {where}")
            chk = re.search(r'<section[^>]*id="check".*?</section>', t, flags=re.S)
            if not chk or chk.group(0).count('class="q"') != 6:
                fails.append(f"check section must hold six questions: {where}")
            levels = set(re.findall(r'class="challenge"[^>]*data-level="(\w+)"', t))
            for need in ("seed", "branch"):
                if need not in levels: fails.append(f"no {need} challenge: {where}")
            for lv in pgd.get("levels", []):
                if lv.lower() not in levels: fails.append(f"leaves.json lists a {lv} challenge the page lacks: {where}")
            for ch in re.finditer(r'<article class="challenge".*?</article>', t, flags=re.S):
                c = ch.group(0)
                if c.count('class="hint"') != 3 or 'class="solution"' not in c or 'class="commit"' not in c:
                    fails.append(f"challenge without three hints, a commit box and a solution: {where}")
            for d in pgd.get("demos", []):
                if f'id="plate-{pgd["number"]}-{d["k"]}"' not in t:
                    fails.append(f"demo anchor plate-{pgd['number']}-{d['k']} missing: {where}")
            for need, why in (('id="next"', "footer promise"), ('class="notes"', "teacher note"),
                              ('../../assets/lesson.js', "lesson.js"), ('../sam.js', "the leaf library")):
                if need not in t: fails.append(f"no {why}: {where}")
            for fn in LIBRARY:
                if re.search(r"(function\s+" + fn + r"\s*\(|(const|let|var)\s+" + fn + r"\s*=)", t):
                    fails.append(f"page redefines library function {fn}: {where}")
            for call in set(re.findall(r"\b(" + "|".join(LIBRARY) + r")\(", re.sub(r"<pre>.*?</pre>", "", t, flags=re.S))):
                if call not in defined and not re.search(r"\.\s*" + call + r"\(", t):
                    fails.append(f"page calls {call}() which sam.js does not define: {where}")

# ------------------------------------------------------------ render

def check_render():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        fails.append("render check requested but playwright is not installed"); return
    import functools, http.server, threading
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k): pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for q in html_pages():
            if q.name == "404.html": continue
            for w in (360, 1280):
                pg = b.new_page(viewport={"width": w, "height": 800})
                errs = []
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errs.append(str(e)))
                path = rel(q)[:-len("index.html")] if q.name == "index.html" else rel(q)
                pg.goto(base + path); pg.wait_for_timeout(300)
                sw = pg.evaluate("document.documentElement.scrollWidth")
                if sw > w: fails.append(f"horizontal scroll at {w}px: {rel(q)} ({sw})")
                if errs: fails.append(f"console errors: {rel(q)} {errs[:2]}")
                pg.close()
        b.close()
    srv.shutdown()

if __name__ == "__main__":
    check_emdash(); check_headers(); check_boundary(); check_links(); check_css_urls(); check_search(); check_lessons()
    if "--render" in sys.argv: check_render()
    if fails:
        print("\n".join(fails)); print(f"{len(fails)} problem(s)"); sys.exit(1)
    print("check pass: clean")
