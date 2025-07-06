import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.db import init_db, save_report_to_db
from app.agents.diff_analyst import diff_analyst_agent
from app.agents.insight_narrator import insight_narrator_agent
import json

print("🔄 Initializing database...")
init_db()

print("🌱 Loading fake GitHub events...")
with open("data/fake_github_events.json") as f:
    events = json.load(f)

state = {"events": events}

# Add fake PR metrics
state["pr_metrics"] = {
    "total_prs": 7,
    "merged_prs": 5,
    "throughput_percent": round((5 / 7) * 100, 1)
}
state["review_latency"] = {
    "avg_review_latency_hours": 3.25
}
state["cycle_time"] = {
    "avg_cycle_time_hours": 6.75
}
state["ci_failures"] = 2
state["mttr_hours"] = 1.5

# Run analysis + summary
state = diff_analyst_agent(state)
state = insight_narrator_agent(state)

print("💾 Seeding summary into database...")
save_report_to_db(state)
print("✅ Done.")
