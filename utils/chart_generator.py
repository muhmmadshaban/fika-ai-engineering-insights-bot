import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import os

def generate_contribution_chart(per_author_diff: dict, filename="contributions.png"):
    if not per_author_diff:
        return None

    authors = list(per_author_diff.keys())
    additions = [v["additions"] for v in per_author_diff.values()]
    deletions = [v["deletions"] for v in per_author_diff.values()]
    total = [a + d for a, d in zip(additions, deletions)]

    # Sort by total contributions
    sorted_data = sorted(zip(authors, total, additions, deletions), key=lambda x: x[1], reverse=True)
    authors, total, additions, deletions = zip(*sorted_data)

    x = range(len(authors))
    bar_width = 0.6

    plt.figure(figsize=(13, 7))
    bars_add = plt.bar(x, additions, bar_width, label='Additions', color='#4CAF50')
    bars_del = plt.bar(x, deletions, bar_width, bottom=additions, label='Deletions', color='#F44336')

    # Add text labels for additions
    for i, bar in enumerate(bars_add):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height / 2, f"+{additions[i]}", ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # Add text labels for deletions
    for i, bar in enumerate(bars_del):
        height = additions[i] + deletions[i]
        plt.text(bar.get_x() + bar.get_width() / 2, additions[i] + deletions[i] / 2, f"-{deletions[i]}", ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # Add total contribution at the top
    for i in x:
        total_val = additions[i] + deletions[i]
        plt.text(i, total_val + 50, str(total_val), ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.xticks(ticks=x, labels=authors, rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.ylabel("Total Contributions", fontsize=12)
    plt.title("📊 Weekly Code Contributions by Author", fontsize=14, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
    return filename
