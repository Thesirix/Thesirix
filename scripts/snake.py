#!/usr/bin/env python3
"""
snake.py — Animated snake SVG from GitHub contribution calendar.
Self-hosted, no Docker / Node.js required.
Inspired by Platane/snk (https://github.com/Platane/snk).

Algorithm:
  1. Fetch contribution grid via GitHub GraphQL API.
  2. Visit every cell with a boustrophedon (zigzag-column) path.
  3. Build the full snake-body chain at each step.
  4. Emit CSS keyframe animations for the grid cells and snake parts.
"""
import os, sys, json, urllib.request

# ── Config ─────────────────────────────────────────────────────────────────────
USERNAME  = os.environ.get("GITHUB_ACTOR", "Thesirix")
TOKEN     = os.environ.get("GITHUB_TOKEN", "")
OUT       = "assets/snake.svg"

CELL      = 16    # px per grid cell
DOT       = 12    # px dot size
DOT_R     = 2     # dot corner radius
STEP_MS   = 100   # ms per animation step
SNAKE_LEN = 4     # number of body segments

LEVEL_MAP = {
    "NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4,
}

# Palette — light default, dark via CSS media query
C_SNAKE   = "#d2a8ff"
C_BORDER  = "#1b1f230a"
DOTS_L    = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
DOTS_D    = ["#161b22", "#01311f", "#034525", "#0f6d31", "#00c647"]
CE_L, CE_D = "#ebedf0", "#161b22"

# ── 1. Fetch contributions ──────────────────────────────────────────────────────
GQL = (
    "query($l:String!){user(login:$l){contributionsCollection{"
    "contributionCalendar{weeks{contributionDays{"
    "contributionLevel weekday}}}}}}"
)
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": GQL, "variables": {"login": USERNAME}}).encode(),
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "snake-readme-py",
    },
)
with urllib.request.urlopen(req) as r:
    resp = json.loads(r.read())

if "errors" in resp:
    sys.exit(f"GraphQL error: {resp['errors']}")

weeks  = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
GRID_W = len(weeks)
GRID_H = 7

grid: dict = {}   # (x, y) → level 0-4
for wx, week in enumerate(weeks):
    for day in week["contributionDays"]:
        grid[(wx, day["weekday"])] = LEVEL_MAP[day["contributionLevel"]]

# ── 2. Boustrophedon path (visits every cell exactly once) ─────────────────────
path = []
for x in range(GRID_W):
    ys = range(GRID_H) if x % 2 == 0 else range(GRID_H - 1, -1, -1)
    for y in ys:
        path.append((x, y))
N = len(path)  # GRID_W * GRID_H

# ── 3. Snake body positions at each step ───────────────────────────────────────
# Lead-in: SNAKE_LEN-1 off-screen positions to the left of the grid (y=0 row)
lead = [(-SNAKE_LEN + 1 + k, 0) for k in range(SNAKE_LEN - 1)]
full = lead + path  # extended trajectory including before entering the grid

# chain[step][part] = (px, py)   (part 0 = head)
chain = [
    [full[SNAKE_LEN - 1 + step - part] for part in range(SNAKE_LEN)]
    for step in range(N)
]

# ── 4. Time at which each colored cell is eaten ─────────────────────────────────
eat_t = {
    path[i]: i / N
    for i in range(N)
    if grid.get(path[i], 0) > 0
}

# ── 5. CSS / SVG helpers ───────────────────────────────────────────────────────
def pct(t: float) -> str:
    return f"{round(t * 100, 3)}%"


def keyframes(name: str, kfs: list) -> str:
    """Generate @keyframes CSS block. kfs = list of (t_float, style_str)."""
    by_s: dict = {}
    for t, s in kfs:
        by_s.setdefault(s, []).append(t)
    inner = "".join(
        ",".join(pct(t) for t in ts) + "{" + s + "}"
        for s, ts in sorted(by_s.items(), key=lambda x: x[1][0])
    )
    return f"@keyframes {name}{{{inner}}}"


def no_interp(pts: list) -> list:
    """
    Remove points that lie on a straight line between their neighbours.
    Mirrors Platane/snk's removeInterpolatedPositions — drastically reduces
    CSS keyframe count for the long straight column traversals.
    Returns list of (original_index, (x, y)).
    """
    out = []
    for i, p in enumerate(pts):
        if i == 0 or i == len(pts) - 1:
            out.append((i, p))
            continue
        (px, py) = pts[i - 1]
        (nx, ny) = pts[i + 1]
        (x,  y)  = p
        if abs((px + nx) / 2 - x) > 0.01 or abs((py + ny) / 2 - y) > 0.01:
            out.append((i, p))
    return out


# ── 6. Generate SVG ────────────────────────────────────────────────────────────
duration = N * STEP_MS
W  = (GRID_W + 2) * CELL
H  = (GRID_H + 5) * CELL
vb = f"{-CELL} {-CELL * 2} {W} {H}"

css: list = []
els: list = []

# CSS color variables (light default + dark-mode override)
dv_l = "".join(f"--c{i}:{c};" for i, c in enumerate(DOTS_L))
dv_d = "".join(f"--c{i}:{c};" for i, c in enumerate(DOTS_D))
css.append(f":root{{--cb:{C_BORDER};--cs:{C_SNAKE};--ce:{CE_L};{dv_l}}}")
css.append(f"@media(prefers-color-scheme:dark){{:root{{--ce:{CE_D};{dv_d}}}}}")

# Grid cell base style
m_dot = (CELL - DOT) / 2
css.append(
    f".c{{shape-rendering:geometricPrecision;fill:var(--ce);"
    f"stroke-width:1px;stroke:var(--cb);"
    f"animation:none {duration}ms linear infinite;"
    f"width:{DOT}px;height:{DOT}px}}"
)

ci = 0
for y in range(GRID_H):
    for x in range(GRID_W):
        lv = grid.get((x, y), 0)
        cx = x * CELL + m_dot
        cy = y * CELL + m_dot
        t  = eat_t.get((x, y))

        if lv > 0 and t is not None:
            # Animated: cell disappears when the snake eats it
            cid = f"c{ci:x}"
            ci += 1
            css.append(keyframes(cid, [
                (max(0.0, t - 1e-4), f"fill:var(--c{lv})"),
                (min(1.0, t + 1e-4), "fill:var(--ce)"),
                (1.0,                "fill:var(--ce)"),
            ]))
            css.append(f".c.{cid}{{fill:var(--c{lv});animation-name:{cid}}}")
            els.append(
                f'<rect class="c {cid}" x="{cx:.1f}" y="{cy:.1f}"'
                f' rx="{DOT_R}" ry="{DOT_R}"/>'
            )
        elif lv > 0:
            # Colored but not on path (shouldn't happen with full boustrophedon)
            els.append(
                f'<rect class="c" x="{cx:.1f}" y="{cy:.1f}"'
                f' rx="{DOT_R}" ry="{DOT_R}" style="fill:var(--c{lv})"/>'
            )
        else:
            els.append(
                f'<rect class="c" x="{cx:.1f}" y="{cy:.1f}"'
                f' rx="{DOT_R}" ry="{DOT_R}"/>'
            )

# Snake body parts (head = part 0, largest; tail = part SNAKE_LEN-1, smallest)
css.append(
    f".s{{shape-rendering:geometricPrecision;fill:var(--cs);"
    f"animation:none linear {duration}ms infinite}}"
)
for pi in range(SNAKE_LEN):
    u  = (1 - min(pi, 4) / 4) ** 2
    sz = u * (CELL * 0.9) + (1 - u) * (DOT * 0.8)
    mg = (CELL - sz) / 2
    rv = min(4.5, 4 * sz / DOT)

    positions = [chain[i][pi] for i in range(N)]  # (px, py) per step
    kf_pts    = no_interp(positions)
    kfs = [
        (idx / N, f"transform:translate({px * CELL}px,{py * CELL}px)")
        for idx, (px, py) in kf_pts
    ]

    sid      = f"s{pi}"
    x0, y0   = positions[0]
    css.append(keyframes(sid, kfs))
    css.append(
        f".s.{sid}{{transform:translate({x0 * CELL}px,{y0 * CELL}px);"
        f"animation-name:{sid}}}"
    )
    els.append(
        f'<rect class="s {sid}" x="{mg:.1f}" y="{mg:.1f}"'
        f' width="{sz:.1f}" height="{sz:.1f}"'
        f' rx="{rv:.1f}" ry="{rv:.1f}"/>'
    )

# Assemble final SVG
style_block = "".join(css)
svg = (
    f'<svg viewBox="{vb}" width="{W}" height="{H}"'
    f' xmlns="http://www.w3.org/2000/svg">'
    f'<desc>Generated with https://github.com/Thesirix/Thesirix</desc>'
    f'<style>{style_block}</style>'
    + "".join(els)
    + "</svg>"
)

os.makedirs("assets", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(
    f"{OUT} written ✓  "
    f"({GRID_W}×{GRID_H} grid, {N} steps, {len(eat_t)} cells eaten)"
)
