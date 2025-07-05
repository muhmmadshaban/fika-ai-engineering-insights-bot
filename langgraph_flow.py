from langgraph.graph import StateGraph
from typing import TypedDict, List, Any

# Step 1: Define the state schema
class DevState(TypedDict, total=False):  # total=False makes keys optional
    events: List[Any]
    summary: str
    total_additions: int
    total_deletions: int
    per_author_diff: dict  # ← ✅ Add this line to preserve author stats
    pr_metrics: dict       # ← (optional) Add if you use it
    review_latency: dict   # ← (optional)
    cycle_time: dict       # ← (optional)
    ci_failures: int       # ← (optional)

# Step 2: Import your agents
from agents.data_harvester import data_harvester_agent
from agents.diff_analyst import diff_analyst_agent
from agents.insight_narrator import insight_narrator_agent

# Step 3: Build the graph with schema
graph = StateGraph(DevState)

graph.add_node("DataHarvester", data_harvester_agent)
graph.add_node("DiffAnalyst", diff_analyst_agent)
graph.add_node("InsightNarrator", insight_narrator_agent)

graph.set_entry_point("DataHarvester")
graph.add_edge("DataHarvester", "DiffAnalyst")
graph.add_edge("DiffAnalyst", "InsightNarrator")

# Step 4: Compile the graph
app = graph.compile()
