from collections import defaultdict

def diff_analyst_agent(state):
    events = state.get("events", [])
    
    total_additions = 0
    total_deletions = 0
    author_stats = defaultdict(lambda: {"additions": 0, "deletions": 0})
    high_churn_prs = []
    ci_failures = 0

    for e in events:
        additions = e.get("additions", 0)
        deletions = e.get("deletions", 0)
        author = e.get("author", "unknown")
        pr_number = e.get("pr_number", None)
        commit_sha = e.get("sha", None)
        ci_failed = e.get("ci_failed", False)

        total_additions += additions
        total_deletions += deletions

        # Per-author stats
        author_stats[author]["additions"] += additions
        author_stats[author]["deletions"] += deletions

        # High churn PRs (you can adjust threshold)
        if (additions + deletions) > 1000 and pr_number:
            high_churn_prs.append({
                "id": f"PR #{pr_number}" if pr_number else commit_sha,
                "author": author,
                "lines_changed": additions + deletions
            })

        # CI Failures
        if ci_failed:
            ci_failures += 1

    # Convert to list for later summarization
    per_author_contribs = [
        {
            "author": a,
            "additions": stats["additions"],
            "deletions": stats["deletions"]
        }
        for a, stats in author_stats.items()
    ]

    # Update state for downstream InsightNarrator
    state.update({
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "per_author_contributions": per_author_contribs,
        "high_churn_prs": high_churn_prs,
        "ci_failures": ci_failures
    })

    return state
