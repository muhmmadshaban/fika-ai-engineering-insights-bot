# === data_harvester_agent ===
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import statistics
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "microsoft/vscode"
BASE_API = f"https://api.github.com/repos/{REPO}"


def paginated_get_recent(url, headers, since_iso, date_key="created_at"):
    all_data = []
    page = 1
    while True:
        paged_url = f"{url}&page={page}" if "?" in url else f"{url}?page={page}"
        response = requests.get(paged_url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not isinstance(data, list) or not data:
            break

        filtered = []
        for item in data:
            item_date = item.get(date_key)
            if item_date and item_date > since_iso:
                filtered.append(item)
            else:
                break

        if not filtered:
            break

        all_data.extend(filtered)
        if len(filtered) < len(data):
            break

        page += 1
    return all_data


def paginated_get(url, headers, max_pages=5):
    all_data = []
    for page in range(1, max_pages + 1):
        paged_url = f"{url}&page={page}" if "?" in url else f"{url}?page={page}"
        response = requests.get(paged_url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not isinstance(data, list) or not data:
            break
        all_data.extend(data)
    return all_data


def fetch_mttr_from_issues(headers):
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    issues_url = f"{BASE_API}/issues?state=closed&labels=incident&per_page=100&sort=created&direction=desc"
    issues = paginated_get_recent(issues_url, headers, since_iso=week_ago, date_key="created_at")

    recovery_durations = []
    for issue in issues:
        created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        closed_at = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
        recovery_time = (closed_at - created_at).total_seconds() / 3600
        recovery_durations.append(recovery_time)

    mttr_hours = round(statistics.mean(recovery_durations), 2) if recovery_durations else None
    return {"mttr_hours": mttr_hours}


def fetch_pr_throughput(headers):
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    url = f"{BASE_API}/pulls?state=all&per_page=100&sort=created&direction=desc"
    prs = paginated_get_recent(url, headers, since_iso=week_ago, date_key="created_at")
    total_prs = len(prs)
    merged_prs = [pr for pr in prs if pr.get("merged_at")]
    throughput = round((len(merged_prs) / total_prs) * 100, 2) if total_prs else 0.0
    return {
        "total_prs": total_prs,
        "merged_prs": len(merged_prs),
        "throughput_percent": throughput,
        "merged_prs_list": merged_prs
    }


def fetch_ci_failures(headers):
    runs = paginated_get(f"{BASE_API}/actions/runs?per_page=100", headers, max_pages=2)
    return {
        "total_runs": len(runs),
        "failed_runs": sum(1 for run in runs if run.get("conclusion") == "failure")
    }


def fetch_review_latency(headers):
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    url = f"{BASE_API}/pulls?state=all&per_page=100&sort=created&direction=desc"
    prs = paginated_get_recent(url, headers, since_iso=week_ago, date_key="created_at")

    total_latency = 0
    count = 0
    for pr in prs:
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        pr_number = pr["number"]
        reviews = requests.get(f"{BASE_API}/pulls/{pr_number}/reviews", headers=headers).json()
        if reviews:
            first_review_time = datetime.fromisoformat(reviews[0]["submitted_at"].replace("Z", "+00:00"))
        else:
            comments = requests.get(f"{BASE_API}/issues/{pr_number}/comments", headers=headers).json()
            if not comments:
                continue
            first_review_time = datetime.fromisoformat(comments[0]["created_at"].replace("Z", "+00:00"))

        latency_hrs = (first_review_time - created).total_seconds() / 3600
        total_latency += latency_hrs
        count += 1

    avg_latency = round(total_latency / count, 2) if count else 0.0
    return {"avg_review_latency_hours": avg_latency}


def fetch_cycle_time(headers):
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    url = f"{BASE_API}/pulls?state=closed&per_page=100&sort=created&direction=desc"
    prs = paginated_get_recent(url, headers, since_iso=week_ago, date_key="created_at")

    recent_prs = [pr for pr in prs if pr.get("merged_at") and pr["created_at"] > week_ago]
    total_cycle_time = 0
    merged_count = 0
    for pr in recent_prs:
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


def fetch_pr_event(pr, headers):
    pr_number = pr["number"]
    files = paginated_get(f"{BASE_API}/pulls/{pr_number}/files", headers, max_pages=1)
    author_login = pr.get("user", {}).get("login") or "Unknown"
    if "bot" in str(author_login).lower():
        return None

    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    files_changed = len(files)

    return {
        "type": "PullRequestEvent",
        "author": author_login,
        "additions": additions,
        "deletions": deletions,
        "files_changed": files_changed,
        "pr_number": pr_number
    }


def data_harvester_agent(state):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    pr_metrics = fetch_pr_throughput(headers)
    review_latency = fetch_review_latency(headers)
    cycle_time = fetch_cycle_time(headers)
    ci_failures = fetch_ci_failures(headers).get("failed_runs", 0)
    mttr = fetch_mttr_from_issues(headers)

    merged_prs = pr_metrics.get("merged_prs_list", [])

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda pr: fetch_pr_event(pr, headers), merged_prs))

    events = [res for res in results if res]

    # Author-level churn aggregation
    per_author_diff = {}
    for event in events:
        author = event["author"]
        if author not in per_author_diff:
            per_author_diff[author] = {
                "additions": 0,
                "deletions": 0,
                "files_touched": 0
            }
        per_author_diff[author]["additions"] += event["additions"]
        per_author_diff[author]["deletions"] += event["deletions"]
        per_author_diff[author]["files_touched"] += event["files_changed"]

    # Churn Outlier Detection
    author_churn = [(author, stats["additions"] + stats["deletions"]) for author, stats in per_author_diff.items()]
    churn_outliers = []
    if author_churn:
        churn_vals = [val for _, val in author_churn]
        mean_churn = statistics.mean(churn_vals)
        stdev_churn = statistics.stdev(churn_vals) if len(churn_vals) > 1 else 0
        churn_outliers = [
            {"author": author, "churn": churn}
            for author, churn in author_churn
            if churn > mean_churn + 2 * stdev_churn
        ]

    state.update({
        "events": events,
        "pr_metrics": pr_metrics,
        "review_latency": review_latency,
        "cycle_time": cycle_time,
        "ci_failures": ci_failures,
        "mttr_hours": mttr,
        "per_author_diff": per_author_diff,
        "churn_outliers": churn_outliers
    })

    return state
