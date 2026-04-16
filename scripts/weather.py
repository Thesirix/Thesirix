#!/usr/bin/env python3
"""Fetches weather from WeatherAPI, generates assets/weather.svg, updates README.md."""

import os, sys, urllib.request, json, re, base64
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
CITY = "Marseille"
DAYS = 3

# ── Fetch weather ─────────────────────────────────────────────────────────────
api_key = os.environ.get("WEATHER_API_KEY")
if not api_key:
    sys.exit("Missing WEATHER_API_KEY env var")

url = (
    "https://api.weatherapi.com/v1/forecast.json"
    f"?key={api_key}&q={CITY}&days={DAYS}&aqi=no&alerts=no"
)
with urllib.request.urlopen(url) as r:
    data = json.loads(r.read())

forecast = data["forecast"]["forecastday"]

# ── Embed weather icons as base64 (GitHub blocks external SVG resources) ──────
def fetch_icon_b64(path: str) -> str:
    full = f"https:{path}" if path.startswith("//") else path
    with urllib.request.urlopen(full) as r:
        return "data:image/png;base64," + base64.b64encode(r.read()).decode()

icons_b64 = [fetch_icon_b64(d["day"]["condition"]["icon"]) for d in forecast]

# ── Cell content ──────────────────────────────────────────────────────────────
def fmt_date(d: str) -> str:
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")

def xe(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

dates      = [fmt_date(d["date"]) for d in forecast]
conditions = [xe(d["day"]["condition"]["text"]) for d in forecast]
temps      = [f"🌡️ {d['day']['mintemp_c']}–{d['day']['maxtemp_c']} °C" for d in forecast]
winds      = [f"↗️ {d['day']['maxwind_kph']} kph" for d in forecast]

# ── Layout ────────────────────────────────────────────────────────────────────
W         = 820          # +20 so right shadow isn't clipped
PAD       = 8
CARD_W    = 784          # fixed card width, leaves 28px right margin for shadow
H_COL     = 140
D_COL     = (CARD_W - H_COL) // 3      # ≈ 214
ROW_H     = [52, 68, 52, 52, 52]       # icon row is taller
INNER_V   = 14
CARD_H    = sum(ROW_H) + INNER_V * 2   # 276 + 28 = 304
TOTAL_H   = PAD * 2 + CARD_H + 8      # minimal vertical bleed

v0    = PAD + INNER_V
row_y = [v0 + sum(ROW_H[:i]) for i in range(5)]
col_x = [PAD, PAD + H_COL, PAD + H_COL + D_COL, PAD + H_COL + D_COL * 2]

# ── Tokyo Night palette ───────────────────────────────────────────────────────
C_CARD    = "#1a1b2e"   # card background  — same as streak card
C_HEADER  = "#13131f"   # label column bg  — darker
C_LABEL   = "#7aa2f7"   # blue   — row labels (Date, Weather…)
C_DATE    = "#bb9af7"   # purple — dates (comme avant, c'était bon)
C_DATA    = "#38bdae"   # teal   — Condition/Temp/Wind values
C_SEP     = "#292e42"   # separator lines

F_SANS    = "Segoe UI, Arial, sans-serif"
F_EMOJI   = "Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, Segoe UI, Arial, sans-serif"

labels = ["Date", "Weather", "Condition", "Temperature", "Wind"]

# ── Build SVG ─────────────────────────────────────────────────────────────────
L = []
L.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{TOTAL_H}">'
)

# Filter: shadow ONLY on the right side.
# x="0%" → filter region starts at left edge of element, clipping any leftward shadow.
# width="120%" → extends only to the right to catch the offset shadow.
L.append(f"""\
  <defs>
    <filter id="sh" x="0%" y="0%" width="114%" height="112%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="9" result="blur"/>
      <feOffset in="blur" dx="5" dy="3" result="shifted"/>
      <feFlood flood-color="#000000" flood-opacity="0.35" result="color"/>
      <feComposite in="color" in2="shifted" operator="in" result="shadow"/>
      <feMerge>
        <feMergeNode in="shadow"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <clipPath id="card">
      <rect x="{PAD}" y="{PAD}" width="{CARD_W}" height="{CARD_H}" rx="14" ry="14"/>
    </clipPath>
  </defs>""")

# Card base
L.append(
    f'  <rect x="{PAD}" y="{PAD}" width="{CARD_W}" height="{CARD_H}" '
    f'rx="14" ry="14" fill="{C_CARD}" filter="url(#sh)"/>'
)
# Header column background
L.append(
    f'  <rect x="{PAD}" y="{PAD}" width="{H_COL}" height="{CARD_H}" '
    f'fill="{C_HEADER}" clip-path="url(#card)"/>'
)

# Row separators
for i in range(1, 5):
    y = v0 + sum(ROW_H[:i])
    L.append(
        f'  <line x1="{PAD}" y1="{y}" x2="{PAD + CARD_W}" y2="{y}" '
        f'stroke="{C_SEP}" stroke-width="1" clip-path="url(#card)"/>'
    )

# Column separators
for x in col_x[1:]:
    L.append(
        f'  <line x1="{x}" y1="{PAD}" x2="{x}" y2="{PAD + CARD_H}" '
        f'stroke="{C_SEP}" stroke-width="1" clip-path="url(#card)"/>'
    )

# Row labels (left column)
for i, label in enumerate(labels):
    cy = row_y[i] + ROW_H[i] // 2
    L.append(
        f'  <text x="{PAD + H_COL // 2}" y="{cy}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'font-family="{F_SANS}" font-size="13" font-weight="600" fill="{C_LABEL}">'
        f'{label}</text>'
    )

# Row 0 — Dates
for i, date in enumerate(dates):
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[0] + ROW_H[0] // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'font-family="{F_SANS}" font-size="13" font-weight="600" fill="{C_DATE}">{date}</text>'
    )

# Row 1 — Weather icons with floating animation
# animate attributeName="y" directly — most reliable SMIL approach for <image>
for i, b64 in enumerate(icons_b64):
    sz    = 46
    cx    = col_x[i + 1] + D_COL // 2
    cy    = row_y[1] + ROW_H[1] // 2
    ix    = cx - sz // 2
    iy    = cy - sz // 2
    begin = f"{i * 0.9:.1f}s"
    L.append(
        f'  <image x="{ix}" y="{iy}" width="{sz}" height="{sz}" '
        f'href="{b64}" clip-path="url(#card)">\n'
        f'    <animate attributeName="y" '
        f'values="{iy};{iy - 6};{iy}" '
        f'dur="2.7s" begin="{begin}" repeatCount="indefinite" '
        f'calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" keyTimes="0;0.5;1"/>\n'
        f'  </image>'
    )

# Row 2 — Condition
for i, cond in enumerate(conditions):
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[2] + ROW_H[2] // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'font-family="{F_SANS}" font-size="13" fill="{C_DATA}">{cond}</text>'
    )

# Row 3 — Temperature (static)
for i, temp in enumerate(temps):
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[3] + ROW_H[3] // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'font-family="{F_EMOJI}" font-size="13" fill="{C_DATA}">{temp}</text>'
    )

# Row 4 — Wind (static)
for i, wind in enumerate(winds):
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[4] + ROW_H[4] // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'font-family="{F_EMOJI}" font-size="13" fill="{C_DATA}">{wind}</text>'
    )

L.append("</svg>")

svg_content = "\n".join(L)

# ── Write SVG ─────────────────────────────────────────────────────────────────
os.makedirs("assets", exist_ok=True)
with open("assets/weather.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("assets/weather.svg written ✓")

# ── Update README.md between markers ─────────────────────────────────────────
with open("README.md", encoding="utf-8") as f:
    readme = f.read()

block = (
    "\n\n"
    '<div align="center">\n'
    '  <img src="assets/weather.svg" alt="Weather Forecast — Marseille"/>\n'
    "</div>\n\n"
)

updated = re.sub(
    r"<!-- WEATHER_START -->.*?<!-- WEATHER_END -->",
    f"<!-- WEATHER_START -->{block}<!-- WEATHER_END -->",
    readme,
    flags=re.DOTALL,
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)
print("README.md updated ✓")
