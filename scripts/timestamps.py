#!/usr/bin/env python3
import re
from datetime import datetime, timezone, timedelta

README = "README.md"

now         = datetime.now(timezone.utc)
next_update = now + timedelta(minutes=30)

last_str = now.strftime("%Y-%m-%d  %H:%M UTC")
next_str = next_update.strftime("%Y-%m-%d  %H:%M UTC")

section = f"""
<div align="center">

---

🕐 **Last update:** &nbsp; `{last_str}`
☀️ **Next update:** &nbsp; `{next_str}`

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
