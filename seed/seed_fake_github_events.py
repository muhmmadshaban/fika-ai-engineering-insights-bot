import random
import uuid
from datetime import datetime, timedelta
import json
import os

# Create fake authors
authors = ["alice", "bob", "charlie", "david", "eve", "frank", "grace"]

def generate_fake_event():
    author = random.choice(authors)
    additions = random.randint(10, 500)
    deletions = random.randint(5, 400)
    created_at = datetime.utcnow() - timedelta(days=random.randint(0, 7))
    review_latency = round(random.uniform(0.5, 10), 2)
    cycle_time = round(random.uniform(2, 20), 2)
    ci_failure = random.choice([True, False, False, False])  # Mostly successful

    return {
        "id": str(uuid.uuid4()),
        "author": author,
        "additions": additions,
        "deletions": deletions,
        "created_at": created_at.isoformat(),
        "review_latency_hours": review_latency,
        "cycle_time_hours": cycle_time,
        "ci_failed": ci_failure,
        "merged": random.choice([True, False])
    }

def generate_dataset(n=50):
    return [generate_fake_event() for _ in range(n)]

def save_to_file(events, path="data/fake_github_events.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(events, f, indent=2)
    print(f"[✓] Seeded {len(events)} fake events into: {path}")

if __name__ == "__main__":
    fake_events = generate_dataset(50)
    save_to_file(fake_events)
