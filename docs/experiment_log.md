# Experiment log — 5 November 2026

- Benchmark: APIB v0.1.0
- Run: `python3 benchmark.py --n-per-seed 600 --seeds 17 29 43 71 101 --out results`
- Episodes: 3,000
- Seeds: 5
- Policies: 4
- Policy evaluations: 12,000
- Conditions: stable 592; empty_nonterminal 592; duplicate_omission 580; missing_page 641; cursor_cycle 595
- Automated tests: 8/8 passed
- Runtime: standard-library simulator; no LLM or external API calls

## Primary result

False-completion rate: first_page_only 100.00%; stop_on_empty 60.33%; follow_cursor 40.60%; count_verified 0.00%.

## Secondary result

Mean coverage: first_page_only 21.91%; stop_on_empty 85.66%; follow_cursor 94.82%; count_verified 94.82%. Mean tool calls: 1.00, 5.15, 5.74, and 5.74 respectively.

## Interpretation

Count reconciliation changes the completion claim, not the amount retrieved: `count_verified` and `follow_cursor` have identical mean coverage, but the former does not report completion when the unique count fails to match the expected total or a cursor cycle prevents normal exhaustion. This is a safety-oriented abstention from a false completeness claim, not a recovery mechanism.
