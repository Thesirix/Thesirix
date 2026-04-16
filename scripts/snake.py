#!/usr/bin/env python3
"""Generates contribution snake SVG via GitHub GraphQL API — no Docker."""

import os, sys, json, urllib.request

USERNAME = os.environ.get("GITHUB_ACTOR", "Thesirix")
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    sys.exit("Missing GITHUB_TOKEN env var")

# ── Fetch contribution calendar via GraphQL ───────────────────────────────────
query = ('{ user(login: "%s") { contributionsCollection {'
         'contributionCalendar { weeks { contributionDays {'
         'contributionCount color } } } } } }') % USERNAME

body = json.dumps({"query": query}).encode()
req  = urllib.request.Request(
    "https://api.github.com/graphql",
    data=body,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type":  "application/json",
        "User-Agent":    "snake-readme-py",
    },
)
with urllib.request.urlopen(req) as r:
    resp = json.loads(r.read())

if "errors" in resp:
    sys.exit(f"GraphQL error: {resp['errors']}")

weeks = (resp["data"]["user"]["contributionsCollection"]
             ["contributionCalendar"]["weeks"])

# ── Build 7 × 52 grid ─────────────────────────────────────────────────────────
COLS, ROWS  = 52, 7
EMPTY_DAY   = {"contributionCount": 0, "color": "#161b22"}

grid = []
for week in weeks:
    days   = week["contributionDays"]
    padded = days + [EMPTY_DAY] * max(0, ROWS - len(days))
    grid.append(padded[:ROWS])
while len(grid) < COLS:
    grid.append([EMPTY_DAY] * ROWS)
grid = grid[-COLS:]          # keep the most recent 52 weeks

# ── Layout ────────────────────────────────────────────────────────────────────
CELL = 11
GAP  = 2
STEP = CELL + GAP
PADX = 10
PADY = 10
W    = PADX * 2 + COLS * STEP
H    = PADY * 2 + ROWS * STEP

BG          = "#0d1117"
EMPTY_COLOR = "#161b22"

# GitHub's default light-mode colors → remap to Tokyo Night dark
LIGHT_REMAP = {
    "#ebedf0": EMPTY_COLOR,
    "#9be9a8": "#0e4429",
    "#40c463": "#006d32",
    "#30a14e": "#26a641",
    "#216e39": "#39d353",
}

def norm_color(c: str) -> str:
    return LIGHT_REMAP.get(c, c or EMPTY_COLOR)

def rx(col: int) -> int:  return PADX + col * STEP
def ry(row: int) -> int:  return PADY + row * STEP
def cx(col: int) -> float: return PADX + col * STEP + CELL / 2
def cy(row: int) -> float: return PADY + row * STEP + CELL / 2

# ── Serpentine path (column-by-column) ───────────────────────────────────────
path: list[tuple[int, int]] = []
for col in range(COLS):
    rows_iter = range(ROWS) if col % 2 == 0 else range(ROWS - 1, -1, -1)
    for row in rows_iter:
        path.append((col, row))

path_index: dict[tuple[int, int], int] = {pos: i for i, pos in enumerate(path)}
N = len(path)  # 364

# ── Animation params ──────────────────────────────────────────────────────────
DUR        = 3.5   # seconds per full loop
SNAKE_LEN  = 10    # number of visible body segments
DT         = DUR / N

# ── Motion path string (head trajectory) ─────────────────────────────────────
pts   = [(cx(c), cy(r)) for c, r in path]
# Close the loop: return to start
pts  += [(cx(path[0][0]), cy(path[0][1]))]
motion_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

# ── SVG ───────────────────────────────────────────────────────────────────────
L: list[str] = []
L.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{H}">'
)

# Background
L.append(f'  <rect width="{W}" height="{H}" fill="{BG}"/>')

# Defs: motion path + head glow filter
L.append('  <defs>')
L.append(f'    <path id="sp" d="{motion_d}" fill="none"/>')
L.append('    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">')
L.append('      <feGaussianBlur in="SourceAlpha" stdDeviation="2.5" result="b"/>')
L.append('      <feFlood flood-color="#7aa2f7" flood-opacity="0.9" result="c"/>')
L.append('      <feComposite in="c" in2="b" operator="in" result="g"/>')
L.append('      <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>')
L.append('    </filter>')
L.append('  </defs>')

# ── Contribution cells (with eating animation) ────────────────────────────────
half = CELL / 2
for ci in range(COLS):
    for ri in range(ROWS):
        day   = grid[ci][ri]
        color = norm_color(day.get("color", ""))
        x, y  = rx(ci), ry(ri)
        idx   = path_index.get((ci, ri))

        if idx is not None and color != EMPTY_COLOR:
            t_eat     = max(0.0010, idx / N)        # normalized [0,1]
            t_recover = min(0.9990, (idx + SNAKE_LEN + 1) / N)
            # discrete: color → EMPTY → color each cycle
            values = f"{color};{EMPTY_COLOR};{color}"
            kt     = f"0;{t_eat:.4f};{t_recover:.4f}"
            L.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">'
                f'<animate attributeName="fill" values="{values}" keyTimes="{kt}" '
                f'dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
                f'</rect>'
            )
        else:
            L.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
            )

# ── Snake body (segments 1..SNAKE_LEN, drawn back-to-front) ──────────────────
BODY_COLORS = [
    "#4c3a6e", "#5c4882", "#6d5797", "#7e66ab", "#8f75bf",
    "#9d83cb", "#aa91d5", "#b79fde", "#c3ade6", "#cebdee",
]

for seg in range(SNAKE_LEN, 0, -1):
    seg_color = BODY_COLORS[min(seg - 1, len(BODY_COLORS) - 1)]
    opacity   = round(0.25 + (SNAKE_LEN - seg) / SNAKE_LEN * 0.75, 2)
    delay     = seg * DT
    L.append(
        f'  <rect x="{-half:.1f}" y="{-half:.1f}" width="{CELL}" height="{CELL}" rx="3" '
        f'fill="{seg_color}" opacity="{opacity}">'
    )
    L.append(
        f'    <animateMotion dur="{DUR}s" begin="-{delay:.3f}s" '
        f'repeatCount="indefinite" calcMode="linear">'
    )
    L.append(f'      <mpath xlink:href="#sp"/>')
    L.append(f'    </animateMotion>')
    L.append(f'  </rect>')

# ── Snake head ────────────────────────────────────────────────────────────────
L.append(
    f'  <rect x="{-half:.1f}" y="{-half:.1f}" width="{CELL}" height="{CELL}" rx="3" '
    f'fill="#7aa2f7" filter="url(#glow)">'
)
L.append(f'  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">')
L.append(f'    <mpath xlink:href="#sp"/>')
L.append(f'  </animateMotion>')
L.append(f'</rect>')

L.append('</svg>')

# ── Write ─────────────────────────────────────────────────────────────────────
os.makedirs("assets", exist_ok=True)
with open("assets/snake.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("assets/snake.svg written ✓")
