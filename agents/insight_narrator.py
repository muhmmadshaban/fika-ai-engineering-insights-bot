import datetime
import json
from utils.llm import generate_summary_via_llm

from db import save_report_to_db

def log_summary(summary: str):
    with open("audit_log.jsonl", "a") as log_file:
        log_file.write(json.dumps({
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": summary
        }) + "\n")

def generate_narrative(insight_data):
    latency = insight_data.get("review_latency", {}).get("avg", 0)
    cycle_time = insight_data.get("cycle_time", {}).get("avg", 0)
    throughput = insight_data.get("pr_metrics", {}).get("pr_throughput", 0)
    failure_rate = insight_data.get("ci_failures", 0)

    return (
        f"📊 *This week in development:*\n"
        f"- Review latency averaged *{latency:.2f} hours*, showing quick turnarounds.\n"
        f"- Cycle time held steady at *{cycle_time:.2f} hours*, indicating consistent delivery.\n"
        f"- *{throughput}%* of PRs were merged, a sign of stable team velocity.\n"
        f"- There were *{failure_rate}* CI failures, showing good test reliability.\n"
    )

def insight_narrator_agent(state):
    additions = state.get('total_additions', 0)
    deletions = state.get('total_deletions', 0)
    pr_metrics = state.get("pr_metrics", {})
    review_latency = state.get("review_latency", {})
    cycle_time = state.get("cycle_time", {})
    ci_failures = state.get("ci_failures", 0)
    per_author = state.get("per_author_diff", {})

    print("👉 per_author inside insight_narrator_agent:", per_author)

    # Format per-author contributions
    if per_author and any(stats['additions'] + stats['deletions'] > 0 for stats in per_author.values()):
        sorted_authors = sorted(
            per_author.items(),
            key=lambda item: item[1]['additions'] + item[1]['deletions'],
            reverse=True
        )
        author_lines = "\n".join(
            [f"    • {author}: +{stats['additions']} / -{stats['deletions']}" for author, stats in sorted_authors]
        )
    else:
        author_lines = "    • No contributions found."

    # Compute PR throughput
    total_prs = pr_metrics.get("total_prs", 0)
    merged_prs = pr_metrics.get("merged_prs", 0)
    throughput = round((merged_prs / total_prs) * 100, 1) if total_prs > 0 else 0.0

    # DORA metrics
    dora_metrics = {
        "Lead Time for Changes": f"{cycle_time.get('avg_cycle_time_hours', 0)} hrs",
        "Deployment Frequency": f"{merged_prs} PRs/week",
        "Change Failure Rate": f"{round((ci_failures / max(total_prs, 1)) * 100, 2)}%",
        "Mean Time to Recovery": "N/A"
    }

    # Compose summary body
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
        f"• :male-technologist: Per-Author Contributions:\n{author_lines}",
        f"\n• 🚀 *DORA Metrics:*"
    ] + [f"    • {key}: {val}" for key, val in dora_metrics.items()]

    if total_prs == 0:
        summary_lines.append("⚠️ No pull requests opened this week.")
    if ci_failures > 3:
        summary_lines.append("❗ High number of CI failures detected.")

    structured_summary = "\n".join(summary_lines)

    # ✅ Generate LLM-based narrative
    llm_input_metrics = {
        "additions": additions,
        "deletions": deletions,
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "review_latency": review_latency.get("avg_review_latency_hours", 0),
        "cycle_time": cycle_time.get("avg_cycle_time_hours", 0),
        "ci_failures": ci_failures,
        "per_author": per_author
    }

    narrative = generate_summary_via_llm(llm_input_metrics)

    # 🧠 Final summary
    final_summary = f"{narrative}\n\n{structured_summary}"

    print("\n=== Weekly Dev Report Summary ===\n")
    print(final_summary)

    # Log for audit
    log_summary(final_summary)

    state["summary"] = final_summary
    save_report_to_db(state)
    return state
