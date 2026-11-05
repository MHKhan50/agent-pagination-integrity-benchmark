# Agent Pagination Integrity: When an Empty Page Is Not the End

*Research note · 5 November 2026 · Muzammal Hussain · Masmatix Innovations*

## Abstract

Tool-using agents frequently retrieve collections through paginated APIs. A partial response is not necessarily a complete collection: cursor-based APIs may return an empty page while still exposing a continuation token, and page sequences can contain duplicates, omissions, or cursor cycles. We introduce the Agent Pagination Integrity Benchmark (APIB) v0.1.0, a deterministic synthetic simulator for evaluating four pagination-control policies across five conditions. The reference experiment contains 3,000 episodes across five random seeds and 12,000 policy evaluations. In this simulator, the `count_verified` policy reduced false-completion rate to 0%, compared with 40.6% for cursor-following without count reconciliation and 60.3% for stop-on-empty. This is a result about the defined simulator and policies, not a measured result for deployed LLM agents. The release includes reproducible Python code, an explicitly self-generated dataset, automated tests, and a Kaggle/Colab-compatible analysis notebook.

## Why this matters

An agent that says it has collected every record may be making a consequential downstream decision: summarising a case file, reconciling transactions, reviewing audit events, or building a report. If it silently stops after a partial page, the final answer can be incomplete while appearing authoritative. Official API documentation makes clear that continuation metadata, rather than the number of items in the current page, determines whether more pages remain. Google Ad Manager explicitly notes that a page may contain zero results and still have a next-page token; Microsoft Graph also documents continuation-token handling and the importance of retaining the last successful token.

## Research question

How often do common pagination-control policies falsely declare a collection complete under empty-but-nonterminal pages, duplicate/omitted records, missing pages, and cursor cycles?

## Method

APIB generates 3,000 deterministic episodes using seeds 17, 29, 43, 71, and 101. Each episode contains 24–60 expected records and a page size of 5–12. Five conditions are represented: stable pagination, empty nonterminal page, duplicate replacing a unique record, missing interior page, and cursor cycle. Four policies are compared: first-page-only, stop-on-empty, follow-cursor, and count-verified. The primary endpoint is false-completion rate. Secondary endpoints are mean coverage, incomplete-detection rate, correct-completion rate, and mean tool calls.

## Results

| Policy | Mean coverage | False-completion rate | Incomplete detection | Mean calls |
|---|---:|---:|---:|---:|
| First page only | 21.91% | 100.00% | 0.00% | 1.00 |
| Stop on empty | 85.66% | 60.33% | 0.00% | 5.15 |
| Follow cursor | 94.82% | 40.60% | 0.00% | 5.74 |
| Count verified | 94.82% | 0.00% | 100.00% | 5.74 |

The count-verified policy did not improve raw collection coverage over follow-cursor; rather, it changed the claim made about completion. When the observed unique-record count did not match the expected total, it withheld a completion claim. This distinction is central: reliable orchestration requires not only retrieving data, but also knowing when retrieval is incomplete.

## Interpretation and limitations

The results support the stated hypothesis within the synthetic environment. They do not establish how often real agents fail at pagination, nor do they prove that expected totals are always available in production APIs. The simulator assumes a known expected count, uses a small set of hand-designed fault modes, and omits network latency, token expiry, rate limits, concurrent mutations, and real LLM decision-making. A next study should add live API adapters, controlled tool-use by local and hosted agents, and paired uncertainty intervals.

## Reproducibility

The code uses Python's standard library only. Run `python3 -m unittest discover -s tests -v` and `python3 benchmark.py --n-per-seed 600 --seeds 17 29 43 71 101 --out results`. The generated episode table is self-generated synthetic data and contains no personal information.

## Resources

- GitHub: to be added after repository creation and push.
- Kaggle dataset: self-generated episode and result files, to be uploaded after GitHub release.
- Kaggle/Google Colab notebook: included in the repository under `notebooks/`.

## References

1. Kehkashan et al. (2026). *From benchmarks to deployment: a comprehensive review of agentic AI evaluation*. Artificial Intelligence Review. https://doi.org/10.1007/s10462-026-11571-0
2. Google Developers. *Pagination — Ad Manager API*. https://developers.google.com/ad-manager/api/beta/pagination
3. Microsoft Learn. *Paging Microsoft Graph data in your app*. https://learn.microsoft.com/en-us/graph/paging
