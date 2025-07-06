import datetime
import json
from app.utils.llm import generate_summary_via_llm
from app.db import save_report_to_db

def log_summary(summary: str):
    with open("audit_log.jsonl", "a") as log_file:
        log_file.write(json.dumps({
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": summary
        }) + "\n")


def generate_narrative(insight_data):
    latency = insight_data.get("review_latency", {}).get("avg_review_latency_hours", 0)
    cycle_time = insight_data.get("cycle_time", {}).get("avg_cycle_time_hours", 0)
    throughput = insight_data.get("pr_metrics", {}).get("throughput_percent", 0)
    failure_rate = insight_data.get("ci_failures", 0)
    per_author = insight_data.get("per_author_diff", {})
    churn_outliers = insight_data.get("churn_outliers", [])

    top_author_line = ""
    if per_author:
        sorted_authors = sorted(
            per_author.items(),
            key=lambda item: item[1]['additions'] + item[1]['deletions'],
            reverse=True
        )
        top_author, stats = sorted_authors[0]
        add, delete = stats["additions"], stats["deletions"]
        files = stats.get("files_touched", "N/A")
        top_author_line = f"- Top contributor: *{top_author}* with +{add} / -{delete} on {files} file(s).\n"

    churn_flag_line = ""
    if churn_outliers:
        names = ", ".join(out['author'] for out in churn_outliers)
        churn_flag_line = f"⚠️ High churn activity detected from: {names}.\n"

    return (
        f"📊 *This week in development:*\n"
        f"- Review latency averaged *{latency:.2f} hours*, showing quick turnarounds.\n"
        f"- Cycle time held steady at *{cycle_time:.2f} hours*, indicating consistent delivery.\n"
        f"- *{throughput}%* of PRs were merged, a sign of stable team velocity.\n"
        f"- There were *{failure_rate}* CI failures, showing good test reliability.\n"
        f"{top_author_line}{churn_flag_line}"
    )


def insight_narrator_agent(state):
    additions = state.get('total_additions') or sum(e['additions'] for e in state.get('events', []))
    deletions = state.get('total_deletions') or sum(e['deletions'] for e in state.get('events', []))
    pr_metrics = state.get("pr_metrics", {})
    review_latency = state.get("review_latency", {})
    cycle_time = state.get("cycle_time", {})
    ci_failures = state.get("ci_failures", 0)
    per_author = state.get("per_author_diff", {})
    churn_outliers = state.get("churn_outliers", [])

    print("👉 per_author inside insight_narrator_agent:", per_author)

    if per_author and any(stats['additions'] + stats['deletions'] > 0 for stats in per_author.values()):
        sorted_authors = sorted(
            per_author.items(),
            key=lambda item: item[1]['additions'] + item[1]['deletions'],
            reverse=True
        )
        author_lines = "\n".join(
            [
                f"    • {author or 'Unknown'}: +{stats['additions']} / -{stats['deletions']}" +
                (f" ({stats['files_touched']} files)" if "files_touched" in stats else "")
                for author, stats in sorted_authors
            ]
        )
    else:
        author_lines = "    • No contributions found."

    total_prs = pr_metrics.get("total_prs", 0)
    merged_prs = pr_metrics.get("merged_prs", 0)
    throughput = round((merged_prs / total_prs) * 100, 1) if total_prs > 0 else 0.0

    mttr = state.get("mttr_hours", None)
    mttr_display = f"{mttr:.2f} hrs" if mttr is not None else "N/A"

    dora_metrics = {
        "Lead Time for Changes": f"{cycle_time.get('avg_cycle_time_hours', 0)} hrs",
        "Deployment Frequency": f"{merged_prs} PRs/week",
        "Change Failure Rate": f"{round((ci_failures / max(total_prs, 1)) * 100, 2)}%",
        "Mean Time to Recovery": mttr_display
    }

    summary_lines = [
        ":bar_chart: *Weekly Dev Report:*",
        f"• Total Additions: {additions}",
        f"• Total Deletions: {deletions}",
        f"• PR Throughput: {throughput}%",
        f"• Total PRs: {total_prs}",
        f"• Merged PRs: {merged_prs}",
        f"• Avg. Review Latency: {review_latency.get('avg_review_latency_hours', 0)} hrs",
        f"• Avg. Cycle Time: {cycle_time.get('avg_cycle_time_hours', 0)} hrs",
        f"• CI Failures: {ci_failures}",
        f"• Per-Author Contributions:\n{author_lines}",
        f"\n• 🚀 *DORA Metrics:*"
    ] + [f"    • {key}: {val}" for key, val in dora_metrics.items()]

    if total_prs == 0:
        summary_lines.append("⚠️ No pull requests opened this week.")
    if ci_failures > 3:
        summary_lines.append("❗ High number of CI failures detected.")
    if churn_outliers:
        churn_summary = "\n• 🔥 *Churn Outliers:*"
        churn_summary += "\n" + "\n".join(
            [
                f"    • {o['author']}: +{o['additions']} / -{o['deletions']} ({o['files_changed']} files)"
                for o in churn_outliers
            ]
        )
        summary_lines.append(churn_summary)



    structured_summary = "\n".join(summary_lines)

    # LLM + fallback narrative
    llm_input_metrics = {
        "additions": additions,
        "deletions": deletions,
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "review_latency": review_latency.get("avg_review_latency_hours", 0),
        "cycle_time": cycle_time.get("avg_cycle_time_hours", 0),
        "ci_failures": ci_failures,
        "per_author": [
            {
                "author": a,
                "additions": d["additions"],
                "deletions": d["deletions"],
                "files_touched": d.get("files_touched", 0)
            }
            for a, d in per_author.items()
        ],
        "churn_outliers": churn_outliers
    }

    narrative = generate_summary_via_llm(llm_input_metrics) or generate_narrative(state)
    final_summary = f"{narrative}\n\n{structured_summary}"

    print("\n=== Weekly Dev Report Summary ===\n")
    print(final_summary)

    log_summary(final_summary)
    state["summary"] = final_summary
    save_report_to_db(state)

    return state
