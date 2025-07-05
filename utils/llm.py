from dotenv import load_dotenv
load_dotenv()

from together import Together

client = Together()  # uses TOGETHER_API_KEY from .env

def generate_summary_via_llm(metrics):
    prompt = f"""Summarize this GitHub engineering activity:
{metrics}

Focus on DORA metrics and team insight. Keep it under 100 words."""

    response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.1",  # You can also try other Together-supported models
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


sample_metrics = {
    "total_additions": 500,
    "total_deletions": 300,
    "pr_metrics": {"total_prs": 20, "merged_prs": 15},
    "review_latency": {"avg_review_latency_hours": 3},
    "cycle_time": {"avg_cycle_time_hours": 9.5},
    "ci_failures": 2,
    "per_author_diff": {
        "alice": {"additions": 300, "deletions": 150},
        "bob": {"additions": 200, "deletions": 150},
    }
}

print(generate_summary_via_llm(sample_metrics))
