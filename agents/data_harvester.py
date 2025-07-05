import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "tensorflow/tensorflow"
USE_FAKE_DATA = False
FAKE_DATA_PATH = "data/fake_github_events.json"

# ----------- HELPER: Fetch PR Throughput -----------
def fetch_pr_throughput(headers):
    url = f"https://api.github.com/repos/{REPO}/pulls?state=all&per_page=100"
    response = requests.get(url, headers=headers)
    prs = response.json() if response.status_code == 200 else []

    total_prs = len(prs)
    merged_prs = sum(1 for pr in prs if pr.get("merged_at"))
    throughput = round((merged_prs / total_prs) * 100, 2) if total_prs else 0.0

    return {
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "throughput_percent": throughput
    }

# ----------- HELPER: Fetch CI Failures -----------
def fetch_ci_failures(headers):
    url = f"https://api.github.com/repos/{REPO}/actions/runs?per_page=100"
    response = requests.get(url, headers=headers)
    runs = response.json().get("workflow_runs", []) if response.status_code == 200 else []

    return {
        "total_runs": len(runs),
        "failed_runs": sum(1 for run in runs if run.get("conclusion") == "failure")
    }

# ----------- HELPER: Fetch Review Latency (with fallback) -----------
def fetch_review_latency(headers):
    url = f"https://api.github.com/repos/{REPO}/pulls?state=all&per_page=30"
    response = requests.get(url, headers=headers)
    prs = response.json() if response.status_code == 200 else []

    total_latency = 0
    count = 0

    for pr in prs:
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        pr_number = pr["number"]

        # Primary: use formal reviews
        reviews_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/reviews"
        reviews_resp = requests.get(reviews_url, headers=headers)
        reviews = reviews_resp.json() if reviews_resp.status_code == 200 else []

        if reviews:
            first_review_time = datetime.fromisoformat(reviews[0]["submitted_at"].replace("Z", "+00:00"))
        else:
            # Fallback: use issue comments
            comments_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
            comments_resp = requests.get(comments_url, headers=headers)
            comments = comments_resp.json() if comments_resp.status_code == 200 else []

            if not comments:
                continue
            first_review_time = datetime.fromisoformat(comments[0]["created_at"].replace("Z", "+00:00"))

        latency_hrs = (first_review_time - created).total_seconds() / 3600
        total_latency += latency_hrs
        count += 1

    avg_latency = round(total_latency / count, 2) if count else 0.0
    return {"avg_review_latency_hours": avg_latency}

# ----------- HELPER: Fetch Cycle Time (with days+hours) -----------
def fetch_cycle_time(headers):
    url = f"https://api.github.com/repos/{REPO}/pulls?state=closed&per_page=50"
    response = requests.get(url, headers=headers)
    prs = response.json() if response.status_code == 200 else []

    total_cycle_time = 0
    merged_count = 0

    for pr in prs:
        if pr.get("merged_at"):
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            cycle_time_hrs = (merged - created).total_seconds() / 3600
            total_cycle_time += cycle_time_hrs
            merged_count += 1

    avg_hrs = round(total_cycle_time / merged_count, 2) if merged_count else 0.0
    avg_days = round(avg_hrs / 24, 2)
    return {
        "avg_cycle_time_hours": avg_hrs,
        "avg_cycle_time_days": avg_days
    }

# ----------- MAIN AGENT -----------
def data_harvester_agent(state):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{REPO}/commits"
    response = requests.get(url, headers=headers)
    commits = response.json() if response.status_code == 200 else []

    author_stats = {}
    total_additions = 0
    total_deletions = 0
    events = []

    for commit in commits[:10]:  # Limit for performance
        sha = commit['sha']
        commit_url = f"https://api.github.com/repos/{REPO}/commits/{sha}"
        commit_details = requests.get(commit_url, headers=headers).json()

        additions = commit_details.get("stats", {}).get("additions", 0)
        deletions = commit_details.get("stats", {}).get("deletions", 0)

        author_data = commit_details.get("author")
        author_login = author_data.get("login") if author_data else None
        author_name = commit_details.get("commit", {}).get("author", {}).get("name")
        author = author_login or author_name or "Unknown"

        if "bot" in str(author).lower():
            continue

        if author not in author_stats:
            author_stats[author] = {"additions": 0, "deletions": 0}
        author_stats[author]["additions"] += additions
        author_stats[author]["deletions"] += deletions

        total_additions += additions
        total_deletions += deletions

        events.append({
            "type": "PushEvent",
            "author": author,
            "additions": additions,
            "deletions": deletions
        })

    # Metrics
    pr_metrics = fetch_pr_throughput(headers)
    review_latency = fetch_review_latency(headers)
    cycle_time = fetch_cycle_time(headers)
    ci_failures = fetch_ci_failures(headers).get("failed_runs", 0)

    # Update state
    state["events"] = events
    state["total_additions"] = total_additions
    state["total_deletions"] = total_deletions
    state["pr_metrics"] = pr_metrics
    state["review_latency"] = review_latency
    state["cycle_time"] = cycle_time
    state["ci_failures"] = ci_failures
    state["per_author_diff"] = author_stats

    print("\n✅ GitHub stats fetched and state updated.")
    print("📊 Author Contributions:", author_stats)
    print("⏱️ Avg Review Latency (hrs):", review_latency["avg_review_latency_hours"])
    print("🕒 Avg Cycle Time:", f"{cycle_time['avg_cycle_time_hours']} hrs / {cycle_time['avg_cycle_time_days']} days")
    return state
