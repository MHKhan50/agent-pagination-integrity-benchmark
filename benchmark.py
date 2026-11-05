"""Agent Pagination Integrity Benchmark (APIB), stdlib-only reference simulator."""
from __future__ import annotations
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

POLICIES = ("first_page_only", "stop_on_empty", "follow_cursor", "count_verified")
SCENARIOS = ("stable", "empty_nonterminal", "duplicate_omission", "missing_page", "cursor_cycle")


def make_episode(seed: int, episode_index: int) -> dict:
    rng = random.Random(seed * 1_000_003 + episode_index * 97 + 41)
    total = rng.randint(24, 60)
    page_size = rng.randint(5, 12)
    ids = ["item_%04d" % i for i in range(total)]
    pages = [ids[i:i + page_size] for i in range(0, total, page_size)]
    scenario = rng.choice(SCENARIOS)
    if scenario == "empty_nonterminal" and len(pages) >= 2:
        insert_at = rng.randint(1, len(pages) - 1)
        pages.insert(insert_at, [])
    elif scenario == "duplicate_omission" and len(pages) >= 2:
        page_index = rng.randint(1, len(pages) - 1)
        pages[page_index][0] = pages[page_index - 1][-1]
    elif scenario == "missing_page" and len(pages) >= 3:
        del pages[rng.randint(1, len(pages) - 2)]

    page_map = {}
    tokens = ["cursor_%03d" % i for i in range(len(pages))]
    for i, token in enumerate(tokens):
        next_token = tokens[i + 1] if i + 1 < len(tokens) else None
        page_map[token] = {"items": list(pages[i]), "next_cursor": next_token}
    if scenario == "cursor_cycle" and len(tokens) >= 2:
        page_map[tokens[-1]]["next_cursor"] = tokens[-2]
    return {
        "episode_id": "s%d_e%04d" % (seed, episode_index),
        "seed": seed,
        "scenario": scenario,
        "expected_total": total,
        "page_size": page_size,
        "first_cursor": tokens[0],
        "pages": page_map,
    }


def run_policy(episode: dict, policy: str, max_calls: int = 100) -> dict:
    if policy not in POLICIES:
        raise ValueError("Unknown policy: %s" % policy)
    cursor = episode["first_cursor"]
    seen_cursors = set()
    returned_ids: List[str] = []
    calls = 0
    exhausted = False
    termination = "max_calls"

    while cursor is not None and calls < max_calls:
        if cursor in seen_cursors:
            termination = "cursor_cycle"
            break
        seen_cursors.add(cursor)
        page = episode["pages"].get(cursor)
        if page is None:
            termination = "invalid_cursor"
            break
        calls += 1
        items = page["items"]
        returned_ids.extend(items)
        next_cursor = page["next_cursor"]

        if policy == "first_page_only":
            termination = "agent_stopped_after_first_page"
            break
        if policy == "stop_on_empty" and len(items) == 0:
            termination = "stopped_on_empty_page"
            exhausted = True  # This is the unsafe assumption being tested.
            break
        cursor = next_cursor
        if cursor is None:
            exhausted = True
            termination = "no_next_cursor"

    unique_ids = set(returned_ids)
    coverage = len(unique_ids) / float(episode["expected_total"])
    if policy == "first_page_only":
        reported_complete = True
    elif policy == "count_verified":
        reported_complete = exhausted and len(unique_ids) == episode["expected_total"]
    else:
        reported_complete = exhausted

    return {
        "episode_id": episode["episode_id"],
        "seed": episode["seed"],
        "scenario": episode["scenario"],
        "policy": policy,
        "expected_total": episode["expected_total"],
        "unique_retrieved": len(unique_ids),
        "raw_items_returned": len(returned_ids),
        "coverage": coverage,
        "calls": calls,
        "reported_complete": int(reported_complete),
        "actual_complete": int(len(unique_ids) == episode["expected_total"]),
        "false_completion": int(reported_complete and len(unique_ids) != episode["expected_total"]),
        "incomplete_detected": int((len(unique_ids) != episode["expected_total"]) and not reported_complete),
        "termination": termination,
    }


def generate_episodes(n_per_seed: int = 600, seeds: Tuple[int, ...] = (17, 29, 43, 71, 101)) -> List[dict]:
    return [make_episode(seed, i) for seed in seeds for i in range(n_per_seed)]


def run_experiment(out_dir: str = "results", n_per_seed: int = 600, seeds: Tuple[int, ...] = (17, 29, 43, 71, 101)) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    episodes = generate_episodes(n_per_seed, seeds)
    rows = [run_policy(ep, policy) for ep in episodes for policy in POLICIES]
    with (out / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["episode_id", "seed", "scenario", "expected_total", "page_size", "first_cursor", "pages_json"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for ep in episodes:
            writer.writerow({"episode_id": ep["episode_id"], "seed": ep["seed"], "scenario": ep["scenario"],
                             "expected_total": ep["expected_total"], "page_size": ep["page_size"],
                             "first_cursor": ep["first_cursor"], "pages_json": json.dumps(ep["pages"], sort_keys=True)})
    with (out / "per_episode_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    metrics = []
    for policy in POLICIES:
        subset = [r for r in rows if r["policy"] == policy]
        incomplete = [r for r in subset if not r["actual_complete"]]
        metrics.append({
            "policy": policy,
            "episodes": len(subset),
            "mean_coverage": sum(r["coverage"] for r in subset) / len(subset),
            "false_completion_rate": sum(r["false_completion"] for r in subset) / len(subset),
            "incomplete_detection_rate": (sum(r["incomplete_detected"] for r in incomplete) / len(incomplete)) if incomplete else 1.0,
            "correct_completion_rate": sum(1 for r in subset if r["actual_complete"] and r["reported_complete"]) / len(subset),
            "mean_tool_calls": sum(r["calls"] for r in subset) / len(subset),
        })
    with (out / "policy_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics[0].keys()))
        writer.writeheader(); writer.writerows(metrics)
    scenario_counts = {s: sum(1 for ep in episodes if ep["scenario"] == s) for s in SCENARIOS}
    summary = {"benchmark": "Agent Pagination Integrity Benchmark", "version": "0.1.0",
               "n_episodes": len(episodes), "seeds": list(seeds), "policies": list(POLICIES),
               "scenario_counts": scenario_counts, "metrics": metrics,
               "interpretation": "Synthetic deterministic policy simulation; not a measurement of deployed LLM agents."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run APIB synthetic benchmark")
    parser.add_argument("--n-per-seed", type=int, default=600)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 29, 43, 71, 101])
    parser.add_argument("--out", default="results")
    args = parser.parse_args()
    result = run_experiment(args.out, args.n_per_seed, tuple(args.seeds))
    print(json.dumps(result, indent=2))
