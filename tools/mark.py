#!/usr/bin/env python3
# සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
"""The sunflower mark, drawn by numbers. This code is MIT; the drawing it makes is the
project's reserved mark (see NOTICES.md).

Seeds sit at the golden angle (Vogel's model: seed n at radius c*sqrt(n), turned n times
137.5 degrees). Each seed carries an arrow. The inner seeds point any way; the outer
seeds line up with one family of spiral arms (seed n points to seed n+8). One arm,
drawn in crimson, runs tip to tail from the centre outward: the spine.

The mark comes in five sizes, each a Fibonacci number of seeds, so that it stays
legible as it shrinks: 55 seeds for large use, 34 for headings, 21 for the top bar,
13 for the footer, 8 for the favicon. As in a real flower head, fewer seeds show a
smaller Fibonacci family of arms (n+5 at 13 seeds, n+3 at 8). Used by tools/build.py.
"""
import math, random

GA = math.radians(137.50776405)          # the golden angle
SIZES = (55, 34, 21, 13, 8)

# width of an arrow as a share of its length, and the share of seeds left scattered
LEAN = {55: 0.24, 34: 0.30, 21: 0.34, 13: 0.38, 8: 0.40}
SCATTER = {55: 0.60, 34: 0.60, 21: 0.40, 13: 0.25, 8: 0.15}
STEP = {55: 8, 34: 8, 21: 8, 13: 5, 8: 3}   # the arm family: seed n points to seed n + STEP
LEVELS = 6                               # colour steps from scattered (0) to aligned (5)

LIGHT = {"field": ("#aeb2c3", "#718ba5"), "shadow": ("#aeb2c3", "#4f6782"), "arm": "#b24d7a", "armshadow": "#8c3a5f"}
DARK = {"field": ("#6d7180", "#9db4cc"), "shadow": ("#3d4047", "#46596d"), "arm": "#d07aa0", "armshadow": "#8c3a5f"}


def _mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(pa[i] + (pb[i] - pa[i]) * t) for i in range(3))


def colours(theme):
    """Variable name -> colour for one theme."""
    out = {}
    for l in range(LEVELS):
        t = l / (LEVELS - 1)
        out[f"--mk{l}"] = _mix(*theme["field"], t)
        out[f"--mk{l}s"] = _mix(*theme["shadow"], t)
    out["--mkc"] = theme["arm"]; out["--mkcs"] = theme["armshadow"]
    return out


def _arrow(x0, y0, x1, y1, w):
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    hl = min(L * 0.42, w * 1.35); hw = w * 1.08; sw = w / 2
    bx, by = x1 - ux * hl, y1 - uy * hl
    return [(x0 + nx * sw, y0 + ny * sw), (bx + nx * sw, by + ny * sw), (bx + nx * hw, by + ny * hw), (x1, y1),
            (bx - nx * hw, by - ny * hw), (bx - nx * sw, by - ny * sw), (x0 - nx * sw, y0 - ny * sw)]


def shapes(N):
    """Draw order: (variable, points, stroke width). The 55-seed drawing is the master."""
    rnd = random.Random(21)
    c = 11.62 * math.sqrt(54.5) / math.sqrt(N - 0.5)
    k = c / 11.62
    pos = lambda n: (c * math.sqrt(n + .5) * math.cos(n * GA), -c * math.sqrt(n + .5) * math.sin(n * GA))
    rmax = c * math.sqrt(N - .5)
    st = STEP[N]
    arm = list(range(2 if st == 8 else 1, N, st))
    lean = LEAN[N] / 0.24
    field, armp = [], []
    for n in range(N):
        if n in arm: continue
        x, y = pos(n); tx, ty = pos(n + st)
        tang = math.atan2(ty - y, tx - x); rr = math.hypot(x, y)
        L = (14 + 6 * rr / rmax) * k; w = L * LEAN[N]
        order = min(1.0, n / (SCATTER[N] * N)) ** 1.3
        ang = tang + math.radians(rnd.uniform(-170, 170)) * (1 - order)
        dx, dy = math.cos(ang) * L / 2, math.sin(ang) * L / 2
        lv = round(order * (LEVELS - 1))
        p = _arrow(x - dx, y - dy, x + dx, y + dy, w)
        field.append((lv, p, [(a + w * .28, b + w * .32) for a, b in p], w))
    for i, n in enumerate(arm):
        x0, y0 = pos(n); x1, y1 = pos(n + st)
        if i == len(arm) - 1: x1, y1 = x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.62
        gx, gy = 0.10 * (x1 - x0), 0.10 * (y1 - y0)
        w = min((4.8 + 2.2 * (i / max(1, len(arm) - 1))) * k * lean, 0.27 * math.hypot(x1 - x0, y1 - y0))
        p = _arrow(x0 + gx, y0 + gy, x1 - gx * .2, y1 - gy * .2, w)
        armp.append((p, [(a + w * .3, b + w * .34) for a, b in p], w))
    out = []
    for lv in range(LEVELS):
        out += [(f"--mk{lv}s", s, w) for l, _, s, w in field if l == lv]
    for lv in range(LEVELS):
        out += [(f"--mk{lv}", p, w) for l, p, _, w in field if l == lv]
    out += [("--mkcs", s, w) for _, s, w in armp]
    out += [("--mkc", p, w) for p, _, w in armp]
    return out


def _box(sh, pad=0.03):
    xs = [x for _, p, _ in sh for x, _ in p]; ys = [y for _, p, _ in sh for _, y in p]
    side = max(max(xs) - min(xs), max(ys) - min(ys)); cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    s = side * (1 + 2 * pad)
    return cx - s / 2, cy - s / 2, s


def _f(v): return ("%.1f" % v).rstrip("0").rstrip(".")


def _body(N, fill):
    """Polygons grouped by colour; fill(var) gives the fill text for a group."""
    sh = shapes(N); parts, cur = [], None
    for var, p, w in sh:
        if var != cur:
            if cur is not None: parts.append("</g>")
            parts.append(f'<g {fill(var)} stroke-linejoin="round">'); cur = var
        pts = " ".join(f"{_f(x)},{_f(y)}" for x, y in p)
        parts.append(f'<polygon points="{pts}" stroke-width="{_f(w * .16)}"/>')
    parts.append("</g>")
    return "".join(parts)


def viewbox(N):
    x, y, s = _box(shapes(N))
    return f"{_f(x)} {_f(y)} {_f(s)} {_f(s)}"


META = ("<metadata>The Sangathika sunflower mark. © 2026 Niranga Dharmaratna. A reserved mark: "
        "not covered by the content or code licences (see NOTICES.md).</metadata>")


def sprite():
    """assets/mark.svg: one symbol per size, coloured by CSS variables set in sam.css,
    with the light colours as fallbacks so the file also draws on its own."""
    lt = colours(LIGHT)
    fill = lambda v: f'style="fill:var({v},{lt[v]});stroke:var({v},{lt[v]})"'
    syms = "\n".join(f'<symbol id="m{N}" viewBox="{viewbox(N)}">{_body(N, fill)}</symbol>' for N in SIZES)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true">\n{META}\n{syms}\n'
            f'<use href="#m55" width="200" height="200"/>\n</svg>\n')


def standalone(N, title="Sangathika"):
    """A self-contained mark (the favicon): fixed colours, with a dark set for dark browsers."""
    lt, dk = colours(LIGHT), colours(DARK)
    cls = {v: f"c{i}" for i, v in enumerate(lt)}
    css = "".join(f".{cls[v]}{{fill:{lt[v]};stroke:{lt[v]}}}" for v in lt)
    css += "@media (prefers-color-scheme:dark){" + "".join(f".{cls[v]}{{fill:{dk[v]};stroke:{dk[v]}}}" for v in dk) + "}"
    body = _body(N, lambda v: f'class="{cls[v]}"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox(N)}" role="img" aria-labelledby="mk-t">'
            f'<title id="mk-t">{title}</title>{META}<style>{css}</style>{body}</svg>\n')


def inline(N, dark=False):
    """A mark with fixed colours for pages rendered off the site (the social cards)."""
    col = colours(DARK if dark else LIGHT)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox(N)}" aria-hidden="true">'
            + _body(N, lambda v: f'fill="{col[v]}" stroke="{col[v]}"') + "</svg>")


def css_vars():
    """The colour variables, for sam.css (light, then dark)."""
    lt, dk = colours(LIGHT), colours(DARK)
    return ("".join(f"{k}:{v};" for k, v in lt.items()), "".join(f"{k}:{v};" for k, v in dk.items()))


if __name__ == "__main__":
    for N in SIZES:
        print(N, "seeds:", len(shapes(N)) // 2, "arrows, viewBox", viewbox(N))
    print(css_vars()[0]); print(css_vars()[1])
