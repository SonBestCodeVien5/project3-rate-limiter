# Standalone trace analyzer

Implemented `scripts/analyze.py` and `scripts/test_analyze.py` for per-case analysis. The analyzer consumes a runner-recorded `policy.json` and load generator trace, emits JSON plus a short Markdown view, and does not mutate source artifacts. Its correctness claims are bounded by recorded initial state, trace coverage, missing decisions, and outage evidence. Fixed Window uses per-instance checks for local mode plus a separate global observed comparison. Token Bucket uses same-millisecond aggregate replay and a token envelope. Outage availability uses legitimate requests actually sent in each phase; stable recovery needs a configured latency threshold and repeated clean windows.

Synthetic unit tests cover Fixed Window overshoot, local versus shared quota, Token Bucket refill and invalid decisions, tied timestamps, missing/fallback evidence, outage denominators, insufficient recovery observations, and invalid policy. Run with `python3 -m unittest discover -s scripts -p 'test_analyze.py' -v`.

The Fixed Window refinement checks observed decisions within a partial epoch when a fresh isolated state and complete raw trace establish the starting count. It keeps `window_complete=false` because client timestamps cannot prove full server-clock coverage. The summary's canceled flag disables exact decision checks; a truncated raw trace fails before output.

These outputs are analysis tooling, not formal experimental conclusions. The runner must establish the policy file from resolved server configuration and record reset state truthfully. The archived bootstrap traces predate that file and therefore are only eligible for exploratory analysis after a separate policy reconstruction; raw archived files remain untouched.
