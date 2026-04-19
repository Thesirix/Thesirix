#!/usr/bin/env python3
import re
from datetime import datetime, timezone, timedelta

README = "README.md"

PARIS = timezone(timedelta(hours=2))  # UTC+2 (heure d'été Paris)

now = datetime.now(timezone.utc).astimezone(PARIS)

# Prochain run du cron Activity (*/30 * * * *) : arrondi au prochain :00 ou :30
minute = now.minute
if minute < 30:
    next_run = now.replace(minute=30, second=0, microsecond=0)
else:
    next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

last_str = now.strftime("%Y-%m-%d  %H:%M (Paris)")
next_str = next_run.strftime("%Y-%m-%d  %H:%M (Paris)")

section = f"""
<div align="center">

---

🕐 **Last update:** &nbsp; `{last_str}`
⏩ **Next update:** &nbsp; `{next_str}`

</div>
"""

START = "<!--TIMESTAMP_START-->"
END   = "<!--TIMESTAMP_END-->"

with open(README, encoding="utf-8") as f:
    readme = f.read()

updated = re.sub(
    re.escape(START) + r".*?" + re.escape(END),
    START + section + END,
    readme,
    flags=re.DOTALL,
)

with open(README, "w", encoding="utf-8") as f:
    f.write(updated)

print(f"✓ Last: {last_str}  |  Next: {next_str}")
