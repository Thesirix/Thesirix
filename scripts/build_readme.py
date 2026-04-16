#!/usr/bin/env python3
"""
build_readme.py — Rebuild README.md from template.

The template (template/README.md.template) is the single source of truth
for all static content.  Dynamic sections (weather, activity) are extracted
from the current README.md and re-injected so their live data is preserved.

Run this script BEFORE the individual update scripts (activity, weather, snake)
so the static structure is always in sync with the template.
"""
import re, sys

TEMPLATE = "template/README.md.template"
README   = "README.md"

# Each tuple: (start_marker, end_marker)
# Content between these markers is preserved from the current README.
DYNAMIC_SECTIONS = [
    ("<!-- WEATHER_START -->",        "<!-- WEATHER_END -->"),
    ("<!--START_SECTION:activity-->", "<!--END_SECTION:activity-->"),
]

# ── Read template ──────────────────────────────────────────────────────────────
with open(TEMPLATE, encoding="utf-8") as f:
    result = f.read()

# ── Read current README to extract dynamic section contents ────────────────────
try:
    with open(README, encoding="utf-8") as f:
        current = f.read()
except FileNotFoundError:
    current = ""
    print("README.md not found — will build from template with empty sections.")

# ── Inject each dynamic section ────────────────────────────────────────────────
for start_m, end_m in DYNAMIC_SECTIONS:
    # Extract existing content (between markers) from current README
    m = re.search(
        re.escape(start_m) + r"(.*?)" + re.escape(end_m),
        current,
        re.DOTALL,
    )
    content = m.group(1) if m else "\n"

    # Replace the (possibly empty) section in the template output
    result = re.sub(
        re.escape(start_m) + r".*?" + re.escape(end_m),
        start_m + content + end_m,
        result,
        flags=re.DOTALL,
    )

# ── Write rebuilt README ───────────────────────────────────────────────────────
with open(README, "w", encoding="utf-8") as f:
    f.write(result)
print("README.md rebuilt from template ✓")
