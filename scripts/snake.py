#!/usr/bin/env python3
"""
snake.py — Animated snake SVG from GitHub contribution calendar.
Self-hosted, no Docker / Node.js required.
Inspired by Platane/snk (https://github.com/Platane/snk).

Algorithm (matches original snk behaviour):
  1. Fetch contribution grid via GitHub GraphQL API.
  2. Visit colored cells level by level (lightest first).
     For each level: BFS from current head toward the NEAREST reachable
     colored cell (nearest in grid-steps, not Manhattan distance).
     The BFS direction order biases exploration rightward then downward,
     reproducing the organic wandering of the original.
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
C_SNAKE        = "#a855f7"          # base fallback (start of gradient)
COLOR_CYCLE_MS = 3000               # snake hue-wave period in ms
C_BORDER  = "#1b1f230a"
DOTS_L    = ["#ebedf0", "#bfdbfe", "#60a5fa", "#2563eb", "#1d4ed8"]
DOTS_D    = ["#161b22", "#051d4d", "#0a3069", "#0969da", "#1f6feb"]
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

# ── 2. Build path  — BFS-to-any, level by level ──────────────────────────────
#
# Key: instead of picking the nearest target by Manhattan distance (which
# degenerates into column-by-column on a rectangular grid), we BFS outward
# from the current head and take the FIRST colored cell we encounter.
# Direction order: right → down → left → up  (matches snk's around4 bias).
# This creates the organic, wandering movement of the original.

# Directions in the same order as snk's around4: right, down, left, up
DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))

eaten: set = set()   # cells already consumed


def is_traversable(x: int, y: int, max_lv: int) -> bool:
    """True if the cell can be crossed when hunting cells of level max_lv."""
    if not (0 <= x < GRID_W and 0 <= y < GRID_H):
        return False
    c = grid.get((x, y), 0)
    return c == 0 or (x, y) in eaten or c <= max_lv


def bfs_to_nearest_target(start: tuple, targets: set, max_lv: int):
    """
    BFS from `start` using DIRS order.
    Returns (target, path_to_target) for the FIRST cell in `targets` found.
    Path includes start and target.
    """
    if start in targets:
        return start, [start]

    parent: dict = {start: None}
    q = deque([start])

    while q:
        pos = q.popleft()
        x, y = pos
        for dx, dy in DIRS:
            nxt = (x + dx, y + dy)
            if nxt in parent:
                continue
            if nxt in targets:
                # Found — reconstruct path
                parent[nxt] = pos
                node, path = nxt, []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                return nxt, path
            if is_traversable(nxt[0], nxt[1], max_lv):
                parent[nxt] = pos
                q.append(nxt)

    return None, None   # no reachable target


# Entry: top-left corner of the grid
head = (0, 0)
path = [head]
# Eat the starting cell immediately if it's colored (prevents infinite loop
# where head==target causes seg=[head] with nothing added to eaten).
if grid.get(head, 0) > 0:
    eaten.add(head)

for lv in range(1, 5):
    # All unvisited cells of this level
    remaining: set = {(x, y) for (x, y), c in grid.items() if c == lv}

    while True:
        reachable = remaining - eaten
        if not reachable:
            break

        target, seg = bfs_to_nearest_target(head, reachable, lv)

        if target is None:
            # Grid is disconnected at this level — force-eat the unreachable cells
            for pos in list(reachable):
                path.append(pos)
                eaten.add(pos)
            break

        # Walk along the BFS path; eat every colored cell we cross
        for pos in seg[1:]:
            path.append(pos)
            if grid.get(pos, 0) > 0:
                eaten.add(pos)

        # CRITICAL: always mark target eaten, even when seg=[head] (head==target).
        # Without this, if the snake is already on a colored cell, seg has only
        # the start position, seg[1:] is empty, nothing gets eaten → infinite loop.
        eaten.add(target)

        head = path[-1]

N = len(path)

# ── 3. Snake body positions at each step ──────────────────────────────────────
sx, sy = path[0]
lead = [(sx - SNAKE_LEN + k, sy) for k in range(SNAKE_LEN - 1)]
full = lead + path   # extended trajectory (off-screen lead-in + grid path)

# chain[step][part] = (px, py)   part 0 = head, SNAKE_LEN-1 = tail
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
    by_s: dict = {}
    for t, s in kfs:
        by_s.setdefault(s, []).append(t)
    inner = "".join(
        ",".join(pct(t) for t in ts) + "{" + s + "}"
        for s, ts in sorted(by_s.items(), key=lambda x: x[1][0])
    )
    return f"@keyframes {name}{{{inner}}}"


def no_interp(pts: list) -> list:
    """Remove points collinear with their neighbours (reduces keyframe count)."""
    out = []
    for i, p in enumerate(pts):
        if i == 0 or i == len(pts) - 1:
            out.append((i, p))
            continue
        px, py = pts[i - 1]
        nx, ny = pts[i + 1]
        x, y   = p
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

dv_l = "".join(f"--c{i}:{c};" for i, c in enumerate(DOTS_L))
dv_d = "".join(f"--c{i}:{c};" for i, c in enumerate(DOTS_D))
css.append(f":root{{--cb:{C_BORDER};--cs:{C_SNAKE};--ce:{CE_L};{dv_l}}}")
css.append(f"@media(prefers-color-scheme:dark){{:root{{--ce:{CE_D};{dv_d}}}}}")

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

css.append(
    f".s{{shape-rendering:geometricPrecision;fill:var(--cs);"
    f"animation:none linear {duration}ms infinite}}"
)
css.append(
    "@keyframes snake-hue{"
    "0%{fill:#a855f7}"
    "33%{fill:#e11d48}"
    "66%{fill:#ef4444}"
    "100%{fill:#a855f7}"
    "}"
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
    delay  = -int(pi / SNAKE_LEN * COLOR_CYCLE_MS)
    css.append(keyframes(sid, kfs))
    css.append(
        f".s.{sid}{{"
        f"transform:translate({x0 * CELL}px,{y0 * CELL}px);"
        f"animation-name:{sid},snake-hue;"
        f"animation-duration:{duration}ms,{COLOR_CYCLE_MS}ms;"
        f"animation-timing-function:linear,linear;"
        f"animation-iteration-count:infinite,infinite;"
        f"animation-delay:0ms,{delay}ms}}"
    )
    els.append(
        f'<rect class="s {sid}" x="{mg:.1f}" y="{mg:.1f}"'
        f' width="{sz:.1f}" height="{sz:.1f}"'
        f' rx="{rv:.1f}" ry="{rv:.1f}"/>'
    )

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
