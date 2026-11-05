# Experimental protocol — APIB v0.1.0

**Date:** 2026-11-05  
**Design:** deterministic synthetic simulation; no external API calls; no LLM inference.

## Hypothesis
A policy that treats an empty page as terminal or trusts cursor exhaustion without reconciling unique item counts will have a higher false-completion rate than a policy that follows cursors, deduplicates IDs, detects cycles, and checks the expected total.

## Experimental units
3,000 independently generated episodes across seeds 17, 29, 43, 71, and 101 (600 episodes per seed). Each episode contains 24–60 expected record IDs, a page size of 5–12, and one of five conditions selected by a seeded pseudorandom generator.

## Conditions
1. `stable`: ordinary cursor chain.
2. `empty_nonterminal`: an empty page occurs before a later page and still contains a continuation cursor.
3. `duplicate_omission`: one record on a later page is replaced by a duplicate from the preceding page, leaving a record absent.
4. `missing_page`: an interior page is omitted from the cursor chain.
5. `cursor_cycle`: the final cursor points back to a previously visited cursor.

## Policies
`first_page_only`, `stop_on_empty`, `follow_cursor`, and `count_verified`, as defined in README.md. Every policy receives the same episode.

## Primary endpoint
False-completion rate across all episodes. Secondary endpoints: mean coverage, incomplete-detection rate, correct-completion rate, and mean tool calls.

## Analysis
Report policy-level descriptive metrics. This v0.1.0 release does not claim inferential significance or population-level generalization. Because all policies are evaluated on the same generated episodes, future work may add paired bootstrap confidence intervals and scenario-stratified comparisons.

## Reproducibility
Python standard library only. The fixed seed list and deterministic generator make the episode set reproducible. Automated tests check deterministic generation, each fault mode, cycle termination, and output generation.

## Validity boundaries
This is a simulator benchmark of explicit pagination policies, not a benchmark of actual autonomous LLM agents. The expected total is treated as available metadata. Live APIs may not expose exact totals; the benchmark does not model token expiry, rate limits, concurrent collection mutation, or network failures. These are candidates for later protocol extensions.
