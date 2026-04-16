#!/usr/bin/env python3
"""Fetches GitHub events and updates README.md between activity markers."""

import os, sys, urllib.request, json, re
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME  = os.environ.get("GITHUB_ACTOR", "Thesirix")
MAX_LINES = 5
TOKEN     = os.environ.get("GITHUB_TOKEN", "")

# ── Fetch events ──────────────────────────────────────────────────────────────
url = f"https://api.github.com/users/{USERNAME}/events?per_page=50"
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
def fmt_event(e: dict) -> str | None:
    # Skip bot-generated events (automated commits from workflows)
    actor = e.get("actor", {}).get("login", "")
    if "[bot]" in actor:
        return None

    t         = e["type"]
    repo      = e["repo"]["name"]
    repo_url  = f"https://github.com/{repo}"
    repo_link = f"[{repo}]({repo_url})"
    p         = e.get("payload", {})

    if t == "PushEvent":
        # payload.size is the real commit count; payload.commits is capped at 20
        n      = p.get("size", len(p.get("commits", [])))
        if n == 0:
            return None  # skip empty / merge-only pushes
        branch = p.get("ref", "").replace("refs/heads/", "")
        return f"🔨 Pushed {n} commit{'s' if n != 1 else ''} to {repo_link} on `{branch}`"

    if t == "CreateEvent":
        ref_type = p.get("ref_type", "")
        ref      = p.get("ref", "")
        if ref_type == "repository":
            return f"🎉 Created repository {repo_link}"
        return f"🎉 Created {ref_type} `{ref}` in {repo_link}"

    if t == "WatchEvent":
        return f"⭐ Starred {repo_link}"

    if t == "ForkEvent":
        return f"🍴 Forked {repo_link}"

    if t == "IssuesEvent":
        action     = p.get("action", "")
        num        = p.get("issue", {}).get("number", "")
        issue_link = f"[#{num}]({repo_url}/issues/{num})"
        return f"🐛 {action.capitalize()} issue {issue_link} in {repo_link}"

    if t == "IssueCommentEvent":
        num        = p.get("issue", {}).get("number", "")
        issue_link = f"[#{num}]({repo_url}/issues/{num})"
        return f"💬 Commented on {issue_link} in {repo_link}"

    if t == "PullRequestEvent":
        action  = p.get("action", "")
        num     = p.get("pull_request", {}).get("number", "")
        pr_link = f"[#{num}]({repo_url}/pull/{num})"
        return f"🔀 {action.capitalize()} PR {pr_link} in {repo_link}"

    if t == "PullRequestReviewEvent":
        num     = p.get("pull_request", {}).get("number", "")
        pr_link = f"[#{num}]({repo_url}/pull/{num})"
        return f"👀 Reviewed PR {pr_link} in {repo_link}"

    if t == "ReleaseEvent":
        tag     = p.get("release", {}).get("tag_name", "")
        rel_url = p.get("release", {}).get("html_url", f"{repo_url}/releases")
        return f"🚀 Released [{tag}]({rel_url}) in {repo_link}"

    if t == "DeleteEvent":
        ref_type = p.get("ref_type", "")
        ref      = p.get("ref", "")
        return f"🗑️ Deleted {ref_type} `{ref}` in {repo_link}"

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
        ago    = time_ago(event.get("created_at", ""))
        suffix = f" — _{ago}_" if ago else ""
        lines.append(f"{len(lines) + 1}. {msg}{suffix}")

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
    sys.exit("ERROR: markers <!--START_SECTION:activity--> not found in README.md")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)
print("README.md updated with recent activity ✓")
