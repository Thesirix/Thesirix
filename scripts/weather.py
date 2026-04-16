#!/usr/bin/env python3
"""Fetches weather from WeatherAPI, generates assets/weather.svg, updates README.md."""

import os, sys, urllib.request, json, re, base64
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
CITY = "Marseille"
DAYS = 3

CONDITION_EMOJI = {
    1000: "☀️",  1003: "⛅",  1006: "☁️",  1009: "☁️",
    1030: "🌫️", 1063: "🌦️", 1066: "🌨️", 1069: "🌨️",
    1072: "🌧️", 1087: "⛈️", 1114: "❄️",  1117: "❄️",
    1135: "🌫️", 1147: "🌫️",
}
for c in (1150,1153,1168,1171,1180,1183,1186,1189,1192,1195,1198,1201,1240,1243,1246):
    CONDITION_EMOJI[c] = "🌧️"
for c in (1204,1207,1237,1249,1252,1261,1264):
    CONDITION_EMOJI[c] = "🌨️"
for c in (1210,1213,1216,1219,1222,1225,1255,1258):
    CONDITION_EMOJI[c] = "❄️"
for c in (1273,1276,1279,1282):
    CONDITION_EMOJI[c] = "⛈️"

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

# ── Prepare cell content ──────────────────────────────────────────────────────
def fmt_date(d: str) -> str:
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")

def xml_esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

dates      = [fmt_date(d["date"]) for d in forecast]
conditions = [xml_esc(d["day"]["condition"]["text"]) for d in forecast]
temps      = [f"🌡️ {d['day']['mintemp_c']}–{d['day']['maxtemp_c']} °C" for d in forecast]
winds      = [f"↗️ {d['day']['maxwind_kph']} kph" for d in forecast]

# ── SVG layout (Tokyo Night) ──────────────────────────────────────────────────
W         = 800
PAD       = 8
CARD_W    = W - PAD * 2
H_COL     = 140                          # label column width
D_COL     = (CARD_W - H_COL) // 3       # ≈ 214 — data column width
ROW_H     = [52, 66, 52, 52, 52]        # row heights (icon row taller)
INNER_PAD = 16                           # vertical padding inside card
CARD_H    = sum(ROW_H) + INNER_PAD * 2  # 274 + 32 = 306
TOTAL_H   = PAD * 2 + CARD_H + 22       # +22 shadow bleed

v0    = PAD + INNER_PAD
row_y = [v0 + sum(ROW_H[:i]) for i in range(5)]
col_x = [PAD, PAD + H_COL, PAD + H_COL + D_COL, PAD + H_COL + D_COL * 2]

# Palette
C_CARD   = "#1e2030"
C_HEADER = "#16171f"
C_FG_H   = "#7aa2f7"
C_DATE   = "#bb9af7"
C_DATA   = "#c0caf5"
C_SEP    = "#2f3354"

FONT_SANS  = "Segoe UI, Arial, sans-serif"
FONT_EMOJI = "Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, Segoe UI, Arial, sans-serif"

labels = ["Date", "Weather", "Condition", "Temperature", "Wind"]

# ── Build SVG ─────────────────────────────────────────────────────────────────
L = []

L.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{TOTAL_H}">'
)

L.append(f"""\
  <defs>
    <filter id="sh" x="-4%" y="-4%" width="108%" height="118%">
      <feDropShadow dx="0" dy="5" stdDeviation="8" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
    <clipPath id="card">
      <rect x="{PAD}" y="{PAD}" width="{CARD_W}" height="{CARD_H}" rx="14" ry="14"/>
    </clipPath>
  </defs>""")

# Card
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

# Header labels
for i, label in enumerate(labels):
    cy = row_y[i] + ROW_H[i] // 2
    cx = PAD + H_COL // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="13" font-weight="600" fill="{C_FG_H}">'
        f'{label}</text>'
    )

# Row 0 — Dates
for i, date in enumerate(dates):
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[0] + ROW_H[0] // 2
    L.append(
        f'  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="13" fill="{C_DATE}">{date}</text>'
    )

# Row 1 — Icons (base64 PNG)
for i, b64 in enumerate(icons_b64):
    sz = 46
    cx = col_x[i + 1] + D_COL // 2
    cy = row_y[1] + ROW_H[1] // 2
    L.append(
        f'  <image x="{cx - sz // 2}" y="{cy - sz // 2}" '
        f'width="{sz}" height="{sz}" href="{b64}" clip-path="url(#card)"/>'
    )

# Rows 2-4 — Text (condition / temperature / wind)
for ri, cells in enumerate((conditions, temps, winds), start=2):
    cy = row_y[ri] + ROW_H[ri] // 2
    for ci, cell in enumerate(cells):
        cx = col_x[ci + 1] + D_COL // 2
        L.append(
            f'  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{FONT_EMOJI}" font-size="13" fill="{C_DATA}">{cell}</text>'
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
