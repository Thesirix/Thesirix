#!/usr/bin/env python3
"""
snake.py — Animated snake SVG from GitHub contribution calendar.
Self-hosted, no Docker / Node.js required.
Inspired by Platane/snk (https://github.com/Platane/snk).

Algorithm:
  1. Fetch contribution grid via GitHub GraphQL API.
  2. Visit colored cells level by level (lightest first) using BFS +
     nearest-neighbour — reproduces the organic wandering of the original snk.
  3. Build the full snake-body chain at each step.
  4. Emit CSS keyframe animations for the grid cells and snake parts.
"""
import os, sys, json, urllib.request, urllib.error
from collections import deque

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
if not TOKEN:
    sys.exit("ERROR: GITHUB_TOKEN environment variable is required.")

GQL = (
    "query($l:String!){user(login:$l){contributionsCollection{"
    "contributionCalendar{weeks{contributionDays{"
    "contributionLevel weekday}}}}}}"
)
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": GQL, "variables": {"l": USERNAME}}).encode(),
    headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "snake-readme-py",
    },
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")
    sys.exit(f"GitHub API error {e.code} {e.reason}: {body}")
except urllib.error.URLError as e:
    sys.exit(f"GitHub API connection error: {e.reason}")

if "errors" in resp:
    sys.exit(f"GraphQL error: {resp['errors']}")
if not resp.get("data", {}).get("user"):
    sys.exit(f"No user data for '{USERNAME}'. Response: {resp}")

weeks  = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
GRID_W = len(weeks)
GRID_H = 7

grid: dict = {}   # (x, y) → level 0-4
for wx, week in enumerate(weeks):
    for day in week["contributionDays"]:
        grid[(wx, day["weekday"])] = LEVEL_MAP[day["contributionLevel"]]

# ── 2. Build path visiting colored cells level by level ──────────────────────────
# Like the original snk: lightest (level-1) cells first, then 2, 3, 4.
# Within each level, nearest-neighbour greedy + BFS navigation.
# This produces the characteristic "wandering" movement — not a simple zigzag.

def bfs_path(start, target, can_pass_fn):
    """Shortest path from start → target using parent-pointer BFS."""
    if start == target:
        return [start]
    parent = {start: None}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (x + dx, y + dy)
            if nxt in parent:
                continue
            if nxt == target:
                parent[nxt] = (x, y)
                # Reconstruct path
                p, result = nxt, []
                while p is not None:
                    result.append(p)
                    p = parent[p]
                result.reverse()
                return result
            if can_pass_fn(nxt[0], nxt[1]):
                parent[nxt] = (x, y)
                q.append(nxt)
    return None  # no path found (should not happen on a well-formed grid)


eaten: set = set()   # cells already consumed


def passable(x, y, max_lv):
    """A cell is traversable if it's in-bounds AND (empty | already eaten | color ≤ max_lv)."""
    if not (0 <= x < GRID_W and 0 <= y < GRID_H):
        return False
    c = grid.get((x, y), 0)
    return c == 0 or (x, y) in eaten or c <= max_lv


head = (0, 0)
path = [head]

for lv in range(1, 5):
    pending = [(x, y) for (x, y), c in grid.items() if c == lv]

    while pending:
        # Drop cells eaten en-route by previous BFS segments
        pending = [t for t in pending if t not in eaten]
        if not pending:
            break

        cx, cy = head
        # Nearest-neighbour: pick the closest remaining target
        pending.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
        tx, ty = pending.pop(0)

        seg = bfs_path((cx, cy), (tx, ty),
                       lambda x, y, lv=lv: passable(x, y, lv))
        if seg:
            for pos in seg[1:]:
                path.append(pos)
                if grid.get(pos, 0) > 0:
                    eaten.add(pos)
            head = path[-1]
        else:
            # Fallback (should be unreachable on a connected grid)
            path.append((tx, ty))
            eaten.add((tx, ty))
            head = (tx, ty)

N = len(path)

# ── 3. Snake body positions at each step ──────────────────────────────────────
# Lead-in: SNAKE_LEN-1 off-screen positions so the body starts fully hidden.
sx, sy = path[0]
lead = [(sx - SNAKE_LEN + k, sy) for k in range(SNAKE_LEN - 1)]
full = lead + path   # extended trajectory

# chain[step][part] = (px, py)   (part 0 = head)
chain = [
    [full[SNAKE_LEN - 1 + step - part] for part in range(SNAKE_LEN)]
    for step in range(N)
]

# ── 4. Time at which each colored cell is eaten ──────────────────────────────
eat_t: dict = {}
for i, pos in enumerate(path):
    if pos not in eat_t and grid.get(pos, 0) > 0:
        eat_t[pos] = i / N

# ── 5. CSS / SVG helpers ──────────────────────────────────────────────────────
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
    Remove points that lie exactly on the straight line between their neighbours.
    Mirrors Platane/snk's removeInterpolatedPositions — reduces CSS keyframe count.
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

    positions = [chain[i][pi] for i in range(N)]
    kf_pts    = no_interp(positions)
    kfs = [
        (idx / N, f"transform:translate({px * CELL}px,{py * CELL}px)")
        for idx, (px, py) in kf_pts
    ]

    sid    = f"s{pi}"
    x0, y0 = positions[0]
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
