#!/usr/bin/env python3
"""Apply the archived post-fix quality rules and retain invalid results."""
import datetime as dt
import json
import math
import pathlib
import sys


def check(case: pathlib.Path) -> dict:
    flags = []
    try:
        s = json.loads((case / "load/summary.json").read_text())
        a = json.loads((case / "analysis.json").read_text())
        c = json.loads((case / "load/metadata.json").read_text())["config"]
        trace = [json.loads(x) for x in (case / "load/requests.jsonl").read_text().splitlines()]
        def epoch(t): return dt.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        sent = [r for r in trace if r.get("sent_at")]
        if not sent: raise ValueError("trace has no sent requests")
        residuals = [abs((epoch(r["sent_at"]) - epoch(r["scheduled_at"])) * 1000 - r["schedule_lag_ms"]) for r in sent]
        latres = [abs((epoch(r["end_at"]) - epoch(r["sent_at"])) * 1000 - r["latency_ms"]) for r in sent]
        if max(residuals + latres) > 5: flags.append("clock")
        if s["generator_dropped"]: flags.append("drops")
        if len({r["request_id"] for r in trace}) != s["scheduled"] or s["scheduled"] != len(trace): flags.append("trace_reconcile")
        if not a["evidence"]["summary_counts_match_trace"]: flags.append("counter_reconcile")
        if s["sent"] != s["scheduled"] - s["generator_dropped"]: flags.append("trace_reconcile")
        api = [v for k, v in a["counter_deltas"].items() if k.startswith("api")]
        b = a["counter_deltas"]["backend"]
        if sum(x["requests"] for x in api) != s["sent"] or sum(x["rejected"] for x in api) != s["http_429"] or b["arrivals"] != s["backend_confirmed_arrivals"] or b["arrivals"] != b["success"] + b["overload"] + b["canceled"]:
            flags.append("counter_reconcile")
        errors = sum(x["limiter_errors"] for x in api)
        if errors: flags.append("healthy_redis_errors")
        duration = c["duration_ns"] / 1e9
        start = epoch(s["started_at"])
        fidelity = []
        for cls in ("legitimate", "abusive"):
            target = c["legitimate_rps"] if cls == "legitimate" else c["rps"] - c["legitimate_rps"]
            if not target: continue
            selected = [r for r in sent if r["client_class"] == cls]
            if not selected: raise ValueError(f"no sent requests for {cls} class")
            actual = sum(0 <= epoch(r["sent_at"]) - start < duration for r in selected) / duration
            lag = sorted(r["schedule_lag_ms"] for r in selected)[math.ceil(.95 * len(selected)) - 1]
            good = abs(actual / target - 1) <= .05 and lag <= min(10, 1000 / target)
            if not good: flags.append("fidelity")
            fidelity.append(dict(client_class=cls, target_rps=target, actual_wall_phase_rps=actual, p95_lag_ms=lag, valid=good))
        if c["profile"] == "normal" and (s["http_429"] or b["overload"]): flags.append("normal_outcome")
        result = dict(case=str(case), profile=c["profile"], flags=sorted(set(flags)), sent=s["sent"], drops=s["generator_dropped"],
                      max_schedule_clock_residual_ms=max(residuals), max_latency_clock_residual_ms=max(latres), limiter_errors=errors,
                      backend=b, oracle=a["oracle"]["status"], summary=s, fidelity=fidelity)
    except (OSError, ValueError, KeyError, TypeError, IndexError, ZeroDivisionError, json.JSONDecodeError) as e:
        result = {"case": str(case), "flags": ["checker_error"], "error": str(e)}
    result["valid"] = not result["flags"]
    try:
        (case / "quality.json").write_text(json.dumps(result, indent=2) + "\n")
    except OSError as e:
        print(f"cannot write quality.json: {e}", file=sys.stderr)
        return {"flags": ["checker_error"], "valid": False}
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check-gate-quality.py CASE_DIR", file=sys.stderr); sys.exit(2)
    result = check(pathlib.Path(sys.argv[1]))
    print(json.dumps({k: result.get(k) for k in ("case", "flags", "valid", "error")}))
    sys.exit(0 if result["valid"] else 1)
