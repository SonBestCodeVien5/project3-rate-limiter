#!/usr/bin/env python3
"""Conservative, standalone analysis of one Project 3 experiment case."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import sys


DECISIONS = {"allow", "reject", "fail-open", "fail-closed", "disabled"}
EVENTS = ("pause_requested", "pause_completed", "unpause_requested", "unpause_completed")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc
    if result.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return result.timestamp()


def millis(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    delta = parsed.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def distribution(records):
    groups = defaultdict(list)
    for row in records:
        if row.get("sent_at") is None:
            outcome = "generator_drop"
        elif row.get("timeout"):
            outcome = "timeout"
        elif row.get("error"):
            outcome = "transport_or_body_error"
        elif row.get("status") == 429:
            outcome = "reject_429"
        elif row.get("status", 0) >= 500:
            outcome = "server_5xx"
        elif 200 <= row.get("status", 0) < 300:
            outcome = "success"
        else:
            outcome = "other_status"
        groups[(row["client_class"], outcome)].append(row)
    return {f"{klass}/{outcome}": {"count": len(rows), "latency_ms": {
        "p50": percentile([r["latency_ms"] for r in rows if r.get("sent_at")], .5),
        "p95": percentile([r["latency_ms"] for r in rows if r.get("sent_at")], .95),
        "p99": percentile([r["latency_ms"] for r in rows if r.get("sent_at")], .99),
    }} for (klass, outcome), rows in sorted(groups.items())}


def load_policy(path):
    p = json.loads(path.read_text())
    if not isinstance(p, dict) or p.get("schema_version") != 1:
        raise ValueError("policy.json requires schema_version=1")
    if p.get("mode") not in ("none", "local", "redis"):
        raise ValueError("policy mode must be none/local/redis")
    if p.get("algorithm") not in ("fixed-window", "token-bucket"):
        raise ValueError("policy algorithm must be fixed-window/token-bucket")
    for name in ("limit", "window_ms", "capacity"):
        if type(p.get(name)) is not int or p[name] <= 0:
            raise ValueError(f"policy {name} must be a positive integer")
    rate = p.get("rate_per_sec")
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
        raise ValueError("policy rate_per_sec must be positive and finite")
    if not isinstance(p.get("namespace"), str) or not p["namespace"].strip():
        raise ValueError("policy namespace must be nonempty")
    if type(p.get("state_reset")) is not bool:
        raise ValueError("policy state_reset must be a boolean")
    if p.get("fail_policy") not in ("open", "closed"):
        raise ValueError("policy fail_policy must be open/closed")
    return p


def load_records(path):
    records, ids = [], set()
    with path.open() as stream:
        for line_no, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("record must be object")
                for field in ("request_id", "client_key", "client_class", "scheduled_at", "end_at"):
                    if not isinstance(row.get(field), str) or not row[field]:
                        raise ValueError(f"missing {field}")
                if row["request_id"] in ids:
                    raise ValueError("duplicate request_id")
                ids.add(row["request_id"])
                if row["client_class"] not in ("legitimate", "abusive"):
                    raise ValueError("invalid client_class")
                for field in ("scheduled_at", "end_at", "sent_at", "decision_at"):
                    if row.get(field):
                        timestamp(row[field])
                if row.get("sent_at") and timestamp(row["end_at"]) < timestamp(row["sent_at"]):
                    raise ValueError("end_at precedes sent_at")
                if type(row.get("status")) is not int or not 0 <= row["status"] <= 599:
                    raise ValueError("status must be integer 0..599")
                if type(row.get("timeout")) is not bool:
                    raise ValueError("timeout must be boolean")
                latency = row.get("latency_ms")
                if type(latency) not in (int, float) or not math.isfinite(latency) or latency < 0:
                    raise ValueError("latency_ms must be finite nonnegative")
                for field in ("instance", "limiter_decision", "decision_at", "error", "phase"):
                    if row.get(field) is not None and not isinstance(row[field], str):
                        raise ValueError(f"{field} must be a string")
                if row.get("limiter_decision") and row["limiter_decision"] not in DECISIONS:
                    raise ValueError("unknown limiter_decision")
                records.append(row)
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    if not records:
        raise ValueError("requests.jsonl is empty")
    return records


def parse_events(path):
    if not path.exists():
        return None
    events = {}
    for line in path.read_text().splitlines():
        match = re.match(r"^(\S+) (pause_requested|pause_completed|unpause_requested|unpause_completed)$", line)
        if match:
            if match[2] in events:
                raise ValueError(f"duplicate outage event {match[2]}")
            events[match[2]] = timestamp(match[1])
    if set(events) != set(EVENTS) or any(events[a] > events[b] for a, b in zip(EVENTS, EVENTS[1:])):
        raise ValueError("outage-events.txt needs four ordered requested/completed events")
    return events


def phase(at, events):
    if at < events["pause_requested"]:
        return "before"
    if at < events["pause_completed"]:
        return "pausing"
    if at < events["unpause_requested"]:
        return "outage"
    if at < events["unpause_completed"]:
        return "unpausing"
    return "after"


def successful(row):
    return row.get("sent_at") is not None and not row.get("error") and not row["timeout"] and 200 <= row["status"] < 300


def outage_analysis(records, events, args, *, measurement_end=None, run_canceled=False):
    if events is None:
        return None
    phases = {}
    for name in ("before", "pausing", "outage", "unpausing", "after"):
        sent = [r for r in records if r.get("sent_at") and phase(timestamp(r["sent_at"]), events) == name]
        legit = [r for r in sent if r["client_class"] == "legitimate"]
        ok = sum(successful(r) for r in legit)
        phases[name] = {"sent": len(sent), "legitimate_sent": len(legit),
                        "legitimate_success": ok, "legitimate_availability": ok / len(legit) if legit else None,
                        "fallback_decisions": sum(r.get("limiter_decision") in ("fail-open", "fail-closed") for r in sent)}
    after = [r for r in records if r.get("sent_at") and timestamp(r["sent_at"]) >= events["unpause_completed"]]
    first = min((timestamp(r["end_at"]) for r in after if r["client_class"] == "legitimate" and successful(r)), default=None)
    recovery = {"first_legitimate_success_after_unpause_ms": max(0, (first - events["unpause_completed"]) * 1000) if first else None,
                "stable_recovery_ms": None, "status": "inconclusive"}
    if run_canceled:
        recovery["reason"] = "run canceled"
    elif measurement_end is None:
        recovery["reason"] = "measurement end unavailable"
    elif args.recovery_p95_ms is None:
        recovery["reason"] = "latency threshold not configured"
    else:
        width = args.recovery_window_ms / 1000
        full_count = max(0, math.floor((measurement_end - events["unpause_completed"]) / width))
        consecutive = 0
        for i in range(full_count):
            lo = events["unpause_completed"] + i * width
            hi = lo + width
            window = [r for r in after if lo <= timestamp(r["sent_at"]) < hi]
            legitimate = [r for r in window if r["client_class"] == "legitimate"]
            clean = len(legitimate) >= args.recovery_min_samples and all(successful(r) for r in legitimate)
            clean = clean and all(r.get("limiter_decision") not in ("fail-open", "fail-closed", None, "") and not r.get("error") and not r["timeout"] and r["status"] < 500 for r in window)
            clean = clean and percentile([r["latency_ms"] for r in legitimate], .95) <= args.recovery_p95_ms if clean else False
            consecutive = consecutive + 1 if clean else 0
            if consecutive >= args.recovery_consecutive:
                recovery["stable_recovery_ms"] = (i + 1) * args.recovery_window_ms
                recovery["status"] = "observed"
                break
        if recovery["status"] == "inconclusive":
            recovery["reason"] = "insufficient consecutive full clean windows"
    return {"events_utc": {k: datetime.fromtimestamp(v, timezone.utc).isoformat() for k, v in events.items()},
            "phase_basis": "sent_at; transition phases kept separate", "phases": phases,
            "fallback_decisions_by_decision_phase": dict(Counter(phase(timestamp(r["decision_at"]), events) for r in records if r.get("limiter_decision") in ("fail-open", "fail-closed") and r.get("decision_at"))),
            "recovery": recovery}


def oracle(records, p, *, trace_complete=False, outage=False, run_canceled=False):
    if p["mode"] == "none":
        return {"status": "not_applicable", "reason": "limiter disabled"}
    groups = defaultdict(list)
    uncertain = defaultdict(set)
    for row in records:
        if not row.get("sent_at"):
            continue  # Generator drops never reach a limiter.
        key = (row["client_key"], row.get("instance") if p["mode"] == "local" else "shared")
        if row.get("limiter_decision") in ("allow", "reject") and row.get("decision_at") and (p["mode"] != "local" or row.get("instance")):
            groups[key].append(row)
        else:
            uncertain[key].add("missing decision/time/instance or fallback")
            if p["mode"] == "local" and not row.get("instance"):
                uncertain[(row["client_key"], "*")].add("unknown target instance")
    results = {"status": "observed", "algorithm": p["algorithm"], "scope": "per instance" if p["mode"] == "local" else "shared", "violations": [], "inconclusive_groups": [], "trace_decision_checks": [], "observed_global_accepted_envelope": []}
    if not any(r.get("sent_at") for r in records):
        results.update(status="inconclusive", reason="no requests reached the limiter", uncertain_keys=0)
        return results
    if not p["state_reset"]:
        results["status"] = "inconclusive"
        results["reason"] = "initial state not established"
    if p["algorithm"] == "fixed-window":
        per_window = defaultdict(list)
        global_window = defaultdict(int)
        for key, rows in groups.items():
            for row in rows:
                w = millis(row["decision_at"]) // p["window_ms"]
                per_window[(key, w)].append(row)
                if row["limiter_decision"] == "allow":
                    global_window[(key[0], w)] += 1
        for (key, window), rows in per_window.items():
            allowed = sum(r["limiter_decision"] == "allow" for r in rows)
            lower = max(0, allowed - p["limit"])
            # A client trace does not establish the observation interval in the
            # server clock domain. Even interior windows remain lower bounds.
            complete = False
            item = {"client_key": key[0], "instance": key[1], "window_start_ms": window * p["window_ms"], "allowed_observed": allowed,
                    "observed_overshoot_lower_bound": lower, "window_complete": complete}
            if lower:
                results["violations"].append({**item, "kind": "observed_allowed_above_quota"})
            # Fresh isolated state starts each epoch at zero. Complete capture of
            # sent requests suffices to check the decisions observed in a partial
            # window, while the window's full traffic remains unobserved.
            checkable = bool(p["state_reset"] and trace_complete and not outage and not run_canceled and
                             key not in uncertain and (key[0], "*") not in uncertain)
            expected = min(len(rows), p["limit"])
            results["trace_decision_checks"].append({**item, "status": "checked" if checkable else "inconclusive",
                "observed_requests": len(rows), "expected_allows_from_fresh_state": expected if checkable else None})
            if checkable and allowed != expected and not lower:
                results["violations"].append({**item, "kind": "fixed_window_decision_mismatch", "expected_allows": expected})
            elif not checkable and any(r["limiter_decision"] == "reject" for r in rows) and allowed < p["limit"]:
                results["inconclusive_groups"].append({**item, "reason": "initial state, missing decision, incomplete trace, outage, or canceled run"})
        results["observed_global_accepted_envelope"] = [{"client_key": key, "window_start_ms": w * p["window_ms"],
            "allowed_observed": count, "shared_quota_overshoot_lower_bound": max(0, count - p["limit"]), "window_complete": False}
            for (key, w), count in sorted(global_window.items())]
    else:
        for key, rows in groups.items():
            ordered = sorted(rows, key=lambda r: millis(r["decision_at"]))
            start = millis(ordered[0]["decision_at"])
            duration = (millis(ordered[-1]["decision_at"]) - start) / 1000
            allowed = sum(r["limiter_decision"] == "allow" for r in rows)
            bound = p["capacity"] + p["rate_per_sec"] * duration
            if allowed > bound + 1e-8:
                results["violations"].append({"client_key": key[0], "instance": key[1], "kind": "accepted_above_token_envelope", "allowed_observed": allowed, "upper_bound": bound})
            if key in uncertain or (key[0], "*") in uncertain or not p["state_reset"] or not trace_complete or outage or run_canceled:
                results["inconclusive_groups"].append({"client_key": key[0], "instance": key[1], "reason": "unknown decision, initial state, incomplete trace, or outage"})
                continue
            # Replay decimal policy semantics exactly, independently of limiter rounding.
            tokens = Fraction(p["capacity"])
            rate = Fraction(str(p["rate_per_sec"]))
            previous = None
            by_ms = defaultdict(list)
            for row in ordered:
                by_ms[millis(row["decision_at"])].append(row)
            for at, batch in sorted(by_ms.items()):
                if previous is not None:
                    tokens = min(p["capacity"], tokens + (at - previous) * rate / 1000)
                available = min(len(batch), max(0, math.floor(tokens)))
                actual = sum(r["limiter_decision"] == "allow" for r in batch)
                if actual != available:
                    results["violations"].append({"client_key": key[0], "instance": key[1], "decision_at_ms": at,
                        "kind": "token_bucket_decision_mismatch", "expected_allows": available, "observed_allows": actual})
                tokens -= actual
                previous = at
        # An envelope is valid for the aggregate regardless of local replay scope.
        by_client = defaultdict(list)
        for (client, _), rows in groups.items():
            by_client[client].extend(r for r in rows if r["limiter_decision"] == "allow")
        for client, rows in sorted(by_client.items()):
            if not rows:
                results["observed_global_accepted_envelope"].append({"client_key": client, "allowed_observed": 0,
                    "single_shared_bucket_upper_bound": None, "above_single_shared_bucket_lower_bound": 0,
                    "status": "no_observed_allows"})
                continue
            times = [millis(r["decision_at"]) for r in rows]
            bound = p["capacity"] + (max(times) - min(times)) * p["rate_per_sec"] / 1000
            results["observed_global_accepted_envelope"].append({"client_key": client, "allowed_observed": len(rows), "single_shared_bucket_upper_bound": bound,
                "above_single_shared_bucket_lower_bound": max(0, math.ceil(len(rows) - bound - 1e-8))})
    if p["algorithm"] == "fixed-window" or uncertain or not p["state_reset"] or not trace_complete or outage or run_canceled or results["inconclusive_groups"]:
        results["status"] = "inconclusive_with_observed_violations" if results["violations"] else "inconclusive"
    elif results["violations"]:
        results["status"] = "observed_violations"
    else:
        results["status"] = "no_violation_observed_within_trace"
    results["uncertain_keys"] = len(uncertain)
    results["coverage_note"] = "Observed counts are lower bounds. FW windows remain partial even when fresh-state trace decisions can be checked; unknown requests, fallback, outage, canceled runs, and absent state reset prevent a complete correctness claim. Equal-ms TB decisions compare aggregate allow counts."
    return results


def counter_delta(case):
    result = {}
    for before in sorted(case.glob("*-before.json")):
        prefix = before.name.removesuffix("-before.json")
        after = case / f"{prefix}-after.json"
        if after.exists():
            a, b = json.loads(before.read_text()), json.loads(after.read_text())
            if not isinstance(a, dict) or not isinstance(b, dict):
                raise ValueError(f"counter snapshot must be JSON object: {before} / {after}")
            result[prefix] = {key: b[key] - a[key] for key in a.keys() & b.keys() if type(a[key]) is int and type(b[key]) is int and key not in ("algorithm",)}
    return result


def redis_resources(path):
    if not path.exists():
        return None
    snapshots = []
    current = None
    for line in path.read_text().splitlines():
        if re.match(r"^\d{4}-\d\d-\d\dT", line):
            if current:
                snapshots.append(current)
            current = {"at": line.strip()}
            timestamp(line.strip())
        elif current is not None:
            match = re.match(r"^(used_cpu_sys|used_cpu_user|used_memory|used_memory_rss):([\d.]+)$", line)
            if match:
                current[match[1]] = float(match[2])
    if current:
        snapshots.append(current)
    if len(snapshots) < 2:
        return {"status": "inconclusive", "reason": "fewer than two Redis resource snapshots"}
    first, last = snapshots[0], snapshots[-1]
    elapsed = timestamp(last["at"]) - timestamp(first["at"])
    result = {"status": "observed", "samples": len(snapshots), "elapsed_seconds": elapsed,
              "memory_bytes_first": first.get("used_memory"), "memory_bytes_last": last.get("used_memory"),
              "rss_bytes_first": first.get("used_memory_rss"), "rss_bytes_last": last.get("used_memory_rss")}
    if elapsed > 0 and all(k in first and k in last for k in ("used_cpu_sys", "used_cpu_user")):
        cpu = last["used_cpu_sys"] + last["used_cpu_user"] - first["used_cpu_sys"] - first["used_cpu_user"]
        result["cpu_seconds_delta"] = cpu
        result["average_cpu_cores"] = cpu / elapsed if cpu >= 0 else None
    return result


def analyze(case, args):
    p = load_policy(case / "policy.json")
    meta = json.loads((case / "load/metadata.json").read_text())
    if not isinstance(meta, dict) or not isinstance(meta.get("config"), dict):
        raise ValueError("metadata.json requires config object")
    rows = load_records(case / "load/requests.jsonl")
    events = parse_events(case / "outage-events.txt")
    labels = meta["config"]
    mismatch = [name for name, field in (("mode", "mode_label"), ("algorithm", "algorithm_label"), ("fail_policy", "fail_policy_label"))
                if labels.get(field) not in (None, "unspecified", p[name])]
    if mismatch:
        raise ValueError(f"metadata labels conflict with recorded policy: {', '.join(mismatch)}")
    sent = [r for r in rows if r.get("sent_at")]
    summary_path = case / "load/summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
    if summary is None or not isinstance(summary, dict):
        raise ValueError("load/summary.json is required to validate trace completeness")
    trace_complete = bool(summary and summary.get("sent") == len(sent) and summary.get("generator_dropped") == len(rows) - len(sent))
    counts = Counter(r.get("limiter_decision") or "unobserved" for r in sent)
    required = ("scheduled", "sent", "generator_dropped")
    if any(type(summary.get(k)) is not int or summary[k] < 0 for k in required):
        raise ValueError("summary requires nonnegative scheduled/sent/generator_dropped")
    if summary["scheduled"] != len(rows) or summary["sent"] != len(sent) or summary["generator_dropped"] != len(rows) - len(sent):
        raise ValueError("summary counts differ from raw requests.jsonl")
    if summary.get("run_id") != labels.get("run_id"):
        raise ValueError("metadata and summary run IDs differ")
    if type(summary.get("canceled")) is not bool:
        raise ValueError("summary canceled must be boolean")
    measurement_end = None
    if events is not None:
        duration = labels.get("duration_ns")
        if isinstance(summary.get("started_at"), str) and type(duration) is int and duration > 0:
            measurement_end = timestamp(summary["started_at"]) + duration / 1e9
    result = {"schema_version": 1, "run_id": labels.get("run_id"), "policy": p,
              "evidence": {"requests": len(rows), "sent": len(sent), "generator_drops": len(rows) - len(sent),
                           "decisions": dict(counts), "trace_has_unknown_decisions": any(r.get("limiter_decision") not in DECISIONS for r in sent),
                           "policy_source": "case/policy.json; runner-recorded server configuration", "run_canceled": summary["canceled"]},
              "distributions": distribution(rows),
              "phase_distributions": {name: distribution([r for r in rows if r.get("phase", "unspecified") == name])
                                      for name in sorted({r.get("phase", "unspecified") for r in rows})},
              "oracle": oracle(rows, p, trace_complete=trace_complete, outage=events is not None, run_canceled=summary["canceled"]),
              "outage": outage_analysis(rows, events, args, measurement_end=measurement_end, run_canceled=summary["canceled"]), "counter_deltas": counter_delta(case),
              "redis_resources": redis_resources(case / "redis-resources.log")}
    result["evidence"]["summary_counts_match_trace"] = trace_complete
    return result


def markdown(result):
    e, o = result["evidence"], result["oracle"]
    lines = [f"# Analysis: {result['run_id'] or 'unnamed run'}", "", "Pilot observation; not a locked research conclusion.", "",
             f"Policy: `{result['policy']['mode']}` / `{result['policy']['algorithm']}`; oracle: **{o['status']}**.", "",
             f"Requests: {e['requests']}; sent: {e['sent']}; generator drops: {e['generator_drops']}.", "",
             f"Observed violations: {len(o.get('violations', []))}. See `analysis.json` for scope and evidence.", ""]
    if result["outage"]:
        outage = result["outage"]
        lines += ["## Redis outage", "", "Availability uses legitimate successes divided by legitimate requests sent in each send-time phase.", ""]
        for phase_name, item in outage["phases"].items():
            lines.append(f"- {phase_name}: {item['legitimate_success']}/{item['legitimate_sent']} legitimate successful/sent; availability {item['legitimate_availability']}.")
        lines += ["", f"Stable recovery: {outage['recovery']['stable_recovery_ms']} ms ({outage['recovery']['status']}).", ""]
    lines += ["Boundary windows, missing decisions and unknown prior state limit correctness claims. TB uses its own token semantics; FW quota is not applied to TB.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--recovery-window-ms", type=int, default=1000)
    parser.add_argument("--recovery-min-samples", type=int, default=5)
    parser.add_argument("--recovery-consecutive", type=int, default=3)
    parser.add_argument("--recovery-p95-ms", type=float)
    args = parser.parse_args()
    if args.recovery_window_ms <= 0 or args.recovery_min_samples <= 0 or args.recovery_consecutive <= 0 or (args.recovery_p95_ms is not None and (not math.isfinite(args.recovery_p95_ms) or args.recovery_p95_ms <= 0)):
        parser.error("recovery parameters must be finite and positive")
    try:
        result = analyze(args.case_dir, args)
        (args.case_dir / "analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        (args.case_dir / "analysis.md").write_text(markdown(result))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 1
    print(f"analysis={args.case_dir / 'analysis.json'} oracle={result['oracle']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
