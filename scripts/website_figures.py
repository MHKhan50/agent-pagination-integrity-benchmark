"""Website figure from results/per_episode_results.csv: false completion by policy and condition.

    python scripts/website_figures.py --out figures_web
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ["first_page_only", "stop_on_empty", "follow_cursor", "count_verified"]
# grey for the stable control, then the house palette
CONDITIONS = [("stable", "#9aa3b2"), ("empty_nonterminal", "#1F4E9C"), ("duplicate_omission", "#E3A800"),
              ("missing_page", "#C8102E"), ("cursor_cycle", "#5FA65A")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="figures_web")
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    fc = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "results" / "per_episode_results.csv")):
        fc[(r["policy"], r["scenario"])].append(int(r["false_completion"]))
    n = len({k for k in fc}) and sum(len(v) for k, v in fc.items() if k[0] == POLICIES[0])
    fig, ax = plt.subplots(figsize=(10, 4.6))
    w = 0.16
    for i, (cond, colour) in enumerate(CONDITIONS):
        vals = [100 * sum(fc[(p, cond)]) / len(fc[(p, cond)]) for p in POLICIES]
        ax.bar([k + (i - 2) * w for k in range(len(POLICIES))], vals, w, color=colour, label=cond.replace("_", " "))
    ax.set_xticks(range(len(POLICIES)), [p.replace("_", " ") for p in POLICIES])
    ax.set_ylabel("false completion (%)")
    ax.set_ylim(0, 105)
    ax.set_title("How often each policy claimed a complete collection when it was not (%s episodes)" % format(n, ","),
                 fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    fig.savefig(out / "agent-pagination-integrity-benchmark.png", dpi=150)
    print("wrote", out / "agent-pagination-integrity-benchmark.png")


if __name__ == "__main__":
    main()
