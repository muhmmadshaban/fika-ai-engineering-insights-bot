# === diff_analyst_agent ===
import statistics
from collections import defaultdict

def diff_analyst_agent(state):
    events = state.get("events", [])

    total_additions = 0
    total_deletions = 0
    author_stats = defaultdict(lambda: {"additions": 0, "deletions": 0, "files_touched": 0})
    churn_list = []
    high_churn_prs = []
    ci_failures = state.get("ci_failures", 0)  # Use existing CI failure count if already computed

    for e in events:
        additions = e.get("additions", 0)
        deletions = e.get("deletions", 0)
        files_changed = e.get("files_changed", 0)
        author = e.get("author", "unknown")

        churn = additions + deletions
        churn_list.append(churn)
        total_additions += additions
        total_deletions += deletions

        author_stats[author]["additions"] += additions
        author_stats[author]["deletions"] += deletions
        author_stats[author]["files_touched"] += files_changed

    mean_churn = statistics.mean(churn_list) if churn_list else 0
    std_churn = statistics.stdev(churn_list) if len(churn_list) > 1 else 1

    # Avoid duplicate outlier entries
    seen_outlier_ids = set()

    for e in events:
        additions = e.get("additions", 0)
        deletions = e.get("deletions", 0)
        churn = additions + deletions
        files_changed = e.get("files_changed", 0)
        author = e.get("author", "unknown")
        pr_number = e.get("pr_number")
        sha = e.get("sha")

        # Create a unique ID
        pr_id = f"PR #{pr_number}" if pr_number else sha

        # Outlier detection with duplicate check
        if std_churn > 0 and (churn - mean_churn) / std_churn > 2 and pr_id not in seen_outlier_ids:
            high_churn_prs.append({
                "id": pr_id,
                "author": author,
                "additions": additions,
                "deletions": deletions,
                "files_changed": files_changed,
                "lines_changed": churn,
                "z_score": round((churn - mean_churn) / std_churn, 2)
            })
            seen_outlier_ids.add(pr_id)

    # Sort per-author contributions by total churn (additions + deletions)
    per_author_contribs = {
        a: stats for a, stats in sorted(
            author_stats.items(),
            key=lambda item: item[1]["additions"] + item[1]["deletions"],
            reverse=True
        )
    }

    # Optional: Sort churn outliers by severity
    high_churn_prs.sort(key=lambda pr: pr["z_score"], reverse=True)

    # Update state
    state.update({
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "per_author_diff": per_author_contribs,
        "churn_outliers": high_churn_prs
    })

    return state
