import sqlite3
from datetime import datetime

DB_PATH = "weekly_reports.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dev_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        total_additions INTEGER,
        total_deletions INTEGER,
        total_prs INTEGER,
        merged_prs INTEGER,
        pr_throughput REAL,
        avg_review_latency REAL,
        avg_cycle_time REAL,
        ci_failures INTEGER,
        per_author TEXT,
        summary TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_report_to_db(state):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    additions = state.get("total_additions", 0)
    deletions = state.get("total_deletions", 0)
    pr = state.get("pr_metrics", {})
    cycle = state.get("cycle_time", {})
    review = state.get("review_latency", {})

    cursor.execute("""
        INSERT INTO dev_reports (
            timestamp, total_additions, total_deletions,
            total_prs, merged_prs, pr_throughput,
            avg_review_latency, avg_cycle_time, ci_failures,
            per_author, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, additions, deletions,
        pr.get("total_prs", 0),
        pr.get("merged_prs", 0),
        round((pr.get("merged_prs", 0) / pr.get("total_prs", 1)) * 100, 1) if pr.get("total_prs", 0) else 0.0,
        review.get("avg_review_latency_hours", 0),
        cycle.get("avg_cycle_time_hours", 0),
        state.get("ci_failures", 0),
        str(state.get("per_author_diff", {})),
        state.get("summary", "")
    ))
    conn.commit()
    conn.close()
