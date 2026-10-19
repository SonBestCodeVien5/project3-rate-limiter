# Portable post-fix measurement gate

This is a repeatable pilot gate, not the locked protocol or a formal benchmark. It preserves the PRESET: Redis Fixed Window, 2 API instances, 5 legitimate keys, Q=B=20, W=1000 ms, refill 20/s, backend capacity 4/service 50 ms, 30 seconds per run, 100 ms Redis bounds, and generator limits from `research-pilot.sh`. It runs normal 20 RPS × 3, then mixed 120 total / 20 legitimate RPS × 3. Quality is checked after each run. A repeated quality flag stops the sequence; invalid runs and logs remain in the unique output directory.

Use a detached clean checkout of the fixed revision and a new output path:

```sh
python3 scripts/observe-clock.py --output artifacts/clock-observe-NEW --duration-seconds 90
```

Inspect `summary.json` first. Proceed to the gate only if `clock_steps_above_5ms` is empty; a detected step means the environment is not ready. The 2026-10-19 observation on the current host failed this check with three realtime jumps of about 2.93–2.96 seconds in 90 seconds ([clock worklog](../worklog/2026-10-19-clock/README.md)), so do not run T03 there.

```sh
bash scripts/run-measurement-gate.sh --output-root artifacts/measurement-gate-NEW --timeout-seconds 240
```

The gate refuses a dirty measurement checkout and any existing output path. Its 240-second per-run bound includes build, startup, load, and cleanup; adjust only before starting if the host requires a longer bound, and record that change. The observer stores `samples.jsonl`, `summary.json`, and `metadata.json`; `clock_steps_above_5ms` reports wall/monotonic divergence. An empty step list only clears this initial check; the run-level gate still checks clock residuals. Neither check nor six passing gate runs locks the research protocol or establishes clock stability beyond the observed interval. Continue T01 environment diagnosis and T03 only after the observer check passes on the measurement host.
