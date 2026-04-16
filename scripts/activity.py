#!/usr/bin/env python3
"""Fetches GitHub public events and updates README.md between activity markers."""

import os, sys, urllib.request, json, re
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME  = os.environ.get("GITHUB_ACTOR", "Thesirix")
MAX_LINES = 5
TOKEN     = os.environ.get("GITHUB_TOKEN", "")

# ── Fetch events ──────────────────────────────────────────────────────────────
url = f"https://api.github.com/users/{USERNAME}/events?per_page=30"
headers = {
    "User-Agent": "activity-readme-py",
    "Accept":     "application/vnd.github+json",
}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    events = json.loads(r.read())

if not isinstance(events, list):
    sys.exit(f"Unexpected API response: {events}")

# ── Format events ─────────────────────────────────────────────────────────────
ICONS = {
    "PushEvent":              "🔨",
    "CreateEvent":            "🎉",
    "DeleteEvent":            "🗑️",
    "WatchEvent":             "⭐",
    "ForkEvent":              "🍴",
    "IssuesEvent":            "🐛",
    "IssueCommentEvent":      "💬",
    "PullRequestEvent":       "🔀",
    "PullRequestReviewEvent": "👀",
    "ReleaseEvent":           "🚀",
}


def fmt_event(e: dict) -> str | None:
    t    = e["type"]
    repo = e["repo"]["name"]
    p    = e.get("payload", {})
    icon = ICONS.get(t, "⚡")

    if t == "PushEvent":
        n      = len(p.get("commits", []))
        branch = p.get("ref", "").replace("refs/heads/", "")
        return f"{icon} Pushed {n} commit{'s' if n != 1 else ''} to `{repo}` on `{branch}`"
    if t == "CreateEvent":
        ref_type = p.get("ref_type", "")
        ref      = p.get("ref", "")
        if ref_type == "repository":
            return f"{icon} Created repository `{repo}`"
        return f"{icon} Created {ref_type} `{ref}` in `{repo}`"
    if t == "WatchEvent":
        return f"{icon} Starred `{repo}`"
    if t == "ForkEvent":
        return f"{icon} Forked `{repo}`"
    if t == "IssuesEvent":
        action = p.get("action", "")
        num    = p.get("issue", {}).get("number", "")
        return f"{icon} {action.capitalize()} issue #{num} in `{repo}`"
    if t == "IssueCommentEvent":
        num = p.get("issue", {}).get("number", "")
        return f"{icon} Commented on issue #{num} in `{repo}`"
    if t == "PullRequestEvent":
        action = p.get("action", "")
        num    = p.get("pull_request", {}).get("number", "")
        return f"{icon} {action.capitalize()} PR #{num} in `{repo}`"
    if t == "ReleaseEvent":
        tag = p.get("release", {}).get("tag_name", "")
        return f"{icon} Released `{tag}` in `{repo}`"
    if t == "DeleteEvent":
        ref_type = p.get("ref_type", "")
        ref      = p.get("ref", "")
        return f"{icon} Deleted {ref_type} `{ref}` in `{repo}`"
    return None


def time_ago(created_at: str) -> str:
    try:
        dt   = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - dt
        days = diff.days
        hrs  = diff.seconds // 3600
        if days >= 1:
            return f"{days}d ago"
        if hrs >= 1:
            return f"{hrs}h ago"
        return "just now"
    except Exception:
        return ""


lines = []
for event in events:
    if len(lines) >= MAX_LINES:
        break
    msg = fmt_event(event)
    if msg:
        ago = time_ago(event.get("created_at", ""))
        suffix = f" — _{ago}_" if ago else ""
        lines.append(f"- {msg}{suffix}")

if not lines:
    print("No recent activity found — README unchanged.")
    sys.exit(0)

# ── Patch README.md ───────────────────────────────────────────────────────────
block = "\n" + "\n".join(lines) + "\n"

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

updated = re.sub(
    r"<!--START_SECTION:activity-->.*?<!--END_SECTION:activity-->",
    f"<!--START_SECTION:activity-->{block}<!--END_SECTION:activity-->",
    readme,
    flags=re.DOTALL,
)

if updated == readme:
    sys.exit("Markers <!--START_SECTION:activity--> not found in README.md")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)
print("README.md updated with recent activity ✓")
