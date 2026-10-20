#!/usr/bin/env python3
"""Validate one formal-study attempt against its locked planned run."""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def stamp(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp lacks timezone")
    return parsed.timestamp()


def read_json(path):
    return json.loads(path.read_text())


def duration_ns(value):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(ns|us|µs|ms|s|m|h)", str(value))
    if not match:
        raise ValueError("unsupported duration: " + str(value))
    scale = {"ns": 1, "us": 1_000, "µs": 1_000, "ms": 1_000_000,
             "s": 1_000_000_000, "m": 60_000_000_000, "h": 3_600_000_000_000}[match[2]]
    return round(float(match[1]) * scale)


def _check(manifest_path, planned_run_id, run_dir):
    """Return validity report; setup/revision failures are fatal and stop the sequence."""
    run_dir = Path(run_dir).resolve()
    reasons, stop = [], False
    def fail(reason, fatal=False):
        nonlocal stop
        reasons.append(reason)
        stop |= fatal
    try:
        manifest = read_json(Path(manifest_path))
        runs = [r for r in manifest["runs"] if r["planned_run_id"] == planned_run_id]
        if len(runs) != 1:
            raise ValueError("planned run ID must match exactly one manifest run")
        planned = runs[0]
        config = planned["config"]
        meta = read_json(run_dir / "load/metadata.json")
        summary = read_json(run_dir / "load/summary.json")
        policy = read_json(run_dir / "policy.json")
        analysis = read_json(run_dir / "analysis.json")
        trace = [json.loads(line) for line in (run_dir / "load/requests.jsonl").read_text().splitlines() if line]
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        return dict(valid=False, stop_sequence=True, reasons=["fatal_setup:" + str(e)])

    # Revision, clean checkout and frozen policy/configuration.
    try:
        evidence_root = run_dir
        while evidence_root != evidence_root.parent and not (evidence_root / "git-revision.txt").exists():
            evidence_root = evidence_root.parent
        revision = (evidence_root / "git-revision.txt").read_text().strip()
        dirty = (evidence_root / "git-status.txt").read_text().strip()
        current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=run_dir, text=True, stderr=subprocess.DEVNULL).strip()
        if revision != planned["source_revision"] or current != revision or meta.get("git_revision") != revision:
            fail("revision_mismatch", True)
        if dirty or meta.get("git_status_porcelain") != "":
            fail("dirty_checkout", True)
    except (OSError, subprocess.SubprocessError):
        fail("revision_evidence_missing", True)
    expected = config["policy"]
    for key, value in expected.items():
        if policy.get(key) != value:
            fail("policy_mismatch:" + key)
    if policy.get("state_reset") is not True:
        fail("state_not_reset")
    c = meta.get("config", {})
    w = config["workload"]
    for key, expected_value in (("profile", "mixed" if w["profile"] == "outage-pair" else w["profile"]),
                                ("duration_ns", w["duration_s"] * 1_000_000_000),
                                ("rps", w["rps"]), ("legitimate_rps", w["legitimate_rps"]),
                                ("legitimate_clients", w["legitimate_clients"]),
                                ("max_inflight", w["max_inflight"]),
                                ("timeout_ns", w["timeout_ms"] * 1_000_000),
                                ("max_schedule_lag_ns", w["max_schedule_lag_ms"] * 1_000_000)):
        if c.get(key) != expected_value:
            fail("workload_config_mismatch:" + key)
    if w["profile"] == "burst":
        for key, value in (("burst_start_ns", w["peak_start_s"] * 1_000_000_000),
                           ("burst_duration_ns", (w["peak_end_s"]-w["peak_start_s"]) * 1_000_000_000),
                           ("burst_rps", w["abusive_peak_rps"])):
            if c.get(key) != value:
                fail("workload_config_mismatch:" + key)
    try:
        topology = read_json(run_dir / "topology/manifest.json")
    except (OSError, ValueError):
        topology = {}
    compose = read_json(run_dir / "compose-resolved.json") if (run_dir / "compose-resolved.json").exists() else {}
    services = compose.get("services", {})
    api_names = sorted(n for n in services if n.startswith("api") and n[3:].isdigit())
    topo = config["topology"]
    if len(api_names) != topo["api_instances"] or not all(n in services for n in ("backend", "redis", "nginx")):
        fail("topology_mismatch")
    for service, pinned in (("redis", "redis:7.4.2-alpine"), ("nginx", "nginx:1.28.0-alpine")):
        images = [services.get(service, {}).get("image")]
        if images != [pinned]:
            fail("pinned_compose_image_mismatch:" + service, True)
    backend_env = services.get("backend", {}).get("environment", {})
    if str(backend_env.get("BACKEND_CAPACITY")) != str(topo["backend_capacity"]) or str(backend_env.get("BACKEND_SERVICE_TIME")) != f'{topo["backend_service_ms"]}ms':
        fail("backend_config_mismatch")
    expected_env = {"MODE": expected["mode"], "ALGORITHM": expected["algorithm"],
                    "FAIL_POLICY": expected["fail_policy"], "LIMIT": str(expected["limit"]),
                    "WINDOW": expected["window_ms"], "CAPACITY": str(expected["capacity"]),
                    "RATE": str(expected["rate_per_sec"])}
    for name in api_names:
        env = services[name].get("environment", {})
        if any((duration_ns(env.get(key)) != value * 1_000_000 if key == "WINDOW" else str(env.get(key)) != str(value)) for key, value in expected_env.items()):
            fail("topology_policy_mismatch:" + name)
    recorded_topology_policy = run_dir / "topology/policy.json"
    if not recorded_topology_policy.exists() or read_json(recorded_topology_policy) != policy:
        fail("topology_policy_evidence_mismatch")
    if len(api_names) == topo["api_instances"]:
        for name in api_names:
            if services[name].get("environment", {}).get("NAMESPACE") != policy.get("namespace"):
                fail("namespace_mismatch:" + name)
    if not (run_dir / "images.json").exists() or not (run_dir / "image-inspect.json").exists() or not (run_dir / "base-image-digests.txt").exists():
        fail("image_identity_evidence_missing")
    else:
        base_digests = (run_dir / "base-image-digests.txt").read_text()
        for digest in ("sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952",
                       "sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284"):
            if digest not in base_digests:
                fail("pinned_base_image_mismatch", True)
        images = read_json(run_dir / "images.json")
        inspect = read_json(run_dir / "image-inspect.json")
        if not isinstance(images, list) or not images or not isinstance(inspect, list) or not inspect:
            fail("image_identity_invalid")
        else:
            inspected_ids = {item.get("Id") for item in inspect if isinstance(item, dict)}
            if any(not image.get("ID") or image["ID"] not in inspected_ids for image in images):
                fail("image_inspect_mismatch")
            inspect_by_id = {item.get("Id"): item for item in inspect if isinstance(item, dict)}
            stable_images = []
            for image in images:
                parts = image.get("ContainerName", "").rsplit("-", 2)
                service = parts[-2] if len(parts) == 3 and parts[-1].isdigit() else ""
                item = inspect_by_id.get(image.get("ID"), {})
                rootfs = item.get("RootFS", {})
                layers = rootfs.get("Layers") if isinstance(rootfs, dict) else None
                if service not in services or not isinstance(layers, list) or not isinstance(item.get("Config"), dict):
                    fail("image_inspect_invalid_or_unmatched")
                    continue
                stable_images.append(dict(service=service, tag=image.get("Tag"), platform=image.get("Platform"),
                                          rootfs=layers, config=item["Config"]))
            image_fingerprint = hashlib.sha256(json.dumps(sorted(stable_images, key=lambda i:i["service"]), sort_keys=True).encode()).hexdigest()

    # Retained trace, IDs, drops and analyzer reconciliation.
    sent_rows = [r for r in trace if r.get("sent_at")]
    drops = summary.get("generator_dropped")
    if summary.get("scheduled") != len(trace) or len({r.get("request_id") for r in trace}) != len(trace):
        fail("trace_count_or_ids")
    if summary.get("sent") != len(sent_rows) or summary.get("sent", 0) + drops != summary.get("scheduled"):
        fail("sent_drop_reconciliation")
    if drops is None:
        fail("generator_drop_count_missing", True)
    elif drops != 0:
        fail("generator_drops")
    if analysis.get("evidence", {}).get("summary_counts_match_trace") is not True:
        fail("analyzer_trace_reconciliation")
    if analysis.get("run_id") != summary.get("run_id") or meta.get("config", {}).get("run_id") != summary.get("run_id"):
        fail("run_id_mismatch")

    # Rate fidelity is evaluated against actual start and the locked phase schedule.
    try:
        start = stamp(summary["started_at"])
        duration = w["duration_s"]
        phase_defs = [(0.0, float(duration), {"legitimate": w["legitimate_rps"], "abusive": w.get("abusive_rps", w.get("abusive_base_rps", 0))})]
        if w["profile"] == "burst":
            begin, end = w["peak_start_s"], w["peak_end_s"]
            phase_defs = [(0., begin, {"legitimate": w["legitimate_rps"], "abusive": w["abusive_base_rps"]}),
                          (begin, end, {"legitimate": w["legitimate_rps"], "abusive": w["abusive_peak_rps"]}),
                          (end, duration, {"legitimate": w["legitimate_rps"], "abusive": w["abusive_base_rps"]})]
        phase_rates = []
        for begin, end, rates in phase_defs:
            for klass, target in rates.items():
                if not target: continue
                rows = [r for r in sent_rows if r.get("client_class") == klass and begin <= stamp(r["sent_at"]) - start < end]
                actual = len(rows) / (end - begin)
                lag = sorted(r["schedule_lag_ms"] for r in rows)[math.ceil(.95 * len(rows)) - 1] if rows else None
                rate_ok = abs(actual / target - 1) <= .05
                lag_ok = lag is not None and lag <= min(10, 1000 / target)
                if not rate_ok: fail(f"rate_fidelity:{klass}:{begin:g}-{end:g}")
                if not lag_ok: fail(f"schedule_lag:{klass}:{begin:g}-{end:g}")
                phase_rates.append(dict(client_class=klass, start_s=begin, end_s=end, target_rps=target, actual_rps=actual, p95_schedule_lag_ms=lag, valid=rate_ok and lag_ok))
        residuals = []
        for r in sent_rows:
            residuals += [abs((stamp(r["sent_at"]) - stamp(r["scheduled_at"])) * 1000 - r["schedule_lag_ms"]),
                          abs((stamp(r["end_at"]) - stamp(r["sent_at"])) * 1000 - r["latency_ms"])]
        max_residual = max(residuals, default=0)
        if max_residual > 5:
            fail("client_clock_residual")
            stop = True
    except (KeyError, TypeError, ValueError, ZeroDivisionError, IndexError):
        fail("trace_timing_invalid", True)
        max_residual, phase_rates = None, []

    deltas = analysis.get("counter_deltas", {})
    api = [v for k, v in deltas.items() if k.startswith("api")]
    backend = deltas.get("backend", {})
    required_counters = set(api_names) | {"backend"}
    if not required_counters.issubset(deltas):
        fail("counter_evidence_missing")
    if sum(x.get("requests", 0) for x in api) != summary.get("sent") or sum(x.get("rejected", 0) for x in api) != summary.get("http_429"):
        fail("api_counter_reconciliation")
    if backend.get("arrivals") != summary.get("backend_confirmed_arrivals") or backend.get("arrivals") != sum(backend.get(k, 0) for k in ("success", "overload", "canceled")):
        fail("backend_counter_reconciliation")
    limiter_errors = sum(x.get("limiter_errors", 0) for x in api)
    outage_attempt = w["profile"] == "outage-pair" and planned["cell"].endswith("outage")
    if limiter_errors and not outage_attempt:
        fail("limiter_errors")
    if w["profile"] == "normal" and (summary.get("http_429") or backend.get("overload")):
        fail("normal_outcome_gate")
    if w["profile"] == "outage-pair":
        if planned["cell"].endswith("healthy"):
            legit = [r for r in sent_rows if r.get("client_class") == "legitimate"]
            legit_ok = [r for r in legit if not r.get("error") and not r.get("timeout") and 200 <= (r.get("status") or 0) < 300]
            if len(legit) != len(legit_ok) or summary.get("legitimate_successful") != len(legit_ok) or summary.get("generator_dropped") or summary.get("transport_errors") or summary.get("timeouts") or sum(x.get("limiter_errors", 0) for x in api) or backend.get("overload"):
                fail("outage_healthy_gate")
        events_file = run_dir / "outage-events.txt"
        if planned["cell"].endswith("outage"):
            try:
                events = [line.split() for line in events_file.read_text().splitlines() if line.strip()]
                names = [e[-1] for e in events]
                required = ["pause_requested", "pause_completed", "unpause_requested", "unpause_completed"]
                times = [stamp(e[0]) for e in events]
                if names != required or times != sorted(times): fail("outage_event_order")
            except (OSError, ValueError, IndexError):
                fail("outage_event_order")
        if planned["cell"].endswith("outage") and not analysis.get("outage"):
            fail("outage_analysis_missing")
    if not isinstance(analysis.get("oracle"), dict) or not analysis.get("oracle", {}).get("status"):
        fail("oracle_status_missing")
    # Redis sampler fields may be null/incomplete by protocol.
    resources = analysis.get("redis_resources")
    if resources is not None and not isinstance(resources, dict): fail("redis_resources_malformed")
    normalized = dict(policy={k:v for k,v in policy.items() if k != "namespace"}, workload=w,
                      topology={"api_instances":len(api_names), "backend_capacity":topo["backend_capacity"],
                                "backend_service_ms":topo["backend_service_ms"]}, image_fingerprint=locals().get("image_fingerprint"))
    config_fingerprint = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    report = dict(valid=not reasons, stop_sequence=stop, reasons=sorted(set(reasons)), planned_run_id=planned_run_id,
                  run_id=summary.get("run_id"), phase_rates=phase_rates, max_wall_monotonic_residual_ms=max_residual,
                  image_fingerprint=locals().get("image_fingerprint"), config_fingerprint=config_fingerprint, oracle_status=analysis.get("oracle", {}).get("status"),
                  limiter_errors=limiter_errors,
                  redis_resources_status=(resources or {}).get("status") if isinstance(resources, dict) else None)
    return report


def check(manifest_path, planned_run_id, run_dir):
    try:
        return _check(manifest_path, planned_run_id, run_dir)
    except (OSError, ValueError, KeyError, TypeError, IndexError, ZeroDivisionError, AttributeError, json.JSONDecodeError) as error:
        return dict(valid=False, stop_sequence=True, reasons=["fatal_artifact:" + str(error)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--planned-run-id", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = check(args.manifest, args.planned_run_id, args.run_dir)
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    except OSError as e:
        print(f"checker output/setup failure: {e}", file=sys.stderr)
        return 2
    print(json.dumps({k: result[k] for k in ("valid", "stop_sequence", "reasons")}))
    return 0 if result["valid"] else (2 if result["stop_sequence"] else 1)


if __name__ == "__main__":
    sys.exit(main())
