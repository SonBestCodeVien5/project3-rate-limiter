#!/usr/bin/env python3
"""Register one Console research case with the local Prometheus file_sd target."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import urlopen


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read(path):
    return json.loads(path.read_text())


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def query(prometheus, expression):
    with urlopen(prometheus.rstrip("/") + "/api/v1/query?" + urlencode({"query": expression}), timeout=2) as response:
        data = json.load(response)
    if data.get("status") != "success":
        raise RuntimeError("Prometheus query failed")
    return data["data"]["result"]


def fresh_scrapes(prometheus, expected, after=None):
    cutoff = max(time.time() - 2, after.timestamp() if after else 0)
    stamps = query(prometheus, 'timestamp(up{job="project3-console-run"} == 1)')
    return {item["metric"].get("service"): datetime.fromtimestamp(float(item["value"][1]), timezone.utc)
            for item in stamps if item["metric"].get("service") in expected
            and float(item["value"][1]) >= cutoff
            and (after is None or float(item["value"][1]) > after.timestamp())}


def scrape_record(scrapes):
    return {service: stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            for service, stamp in scrapes.items()}


def register(args):
    if args.path.exists():
        raise RuntimeError("stale or active target manifest exists; inspect ownership before removing it")
    deadline = time.monotonic() + args.timeout
    while query(args.prometheus, 'up{job="project3-console-run"}'):
        if time.monotonic() >= deadline:
            raise RuntimeError("previous Console scrape series remain visible; refusing a potentially mixed time window")
        time.sleep(0.25)
    services = [*(f"api{i}" for i in range(1, args.instances + 1)), "backend"]
    targets = [{"targets": [f"console-{service}:8080"], "labels": {"service": service,
               "topology": str(args.instances), "project": "project3-research-lab"}} for service in services]
    record = {"owner": args.owner, "registered_at": utc(), "targets": targets,
              "services": services, "instances": args.instances}
    atomic_json(args.record, record)
    args.path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=args.path.parent, prefix=".console-targets-", delete=False) as manifest:
        tmp = Path(manifest.name)
        manifest.write(json.dumps(targets, indent=2) + "\n")
    try:
        os.link(tmp, args.path)
    finally:
        tmp.unlink(missing_ok=True)


def verify_manifest(args, record):
    if record.get("owner") != args.owner or not args.path.exists() or read(args.path) != record.get("targets"):
        raise RuntimeError("target manifest ownership mismatch")


def wait_for_targets(args):
    record = read(args.record)
    verify_manifest(args, record)
    expected = set(record["services"])
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        scrapes = fresh_scrapes(args.prometheus, expected)
        if expected <= scrapes.keys():
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("allowlisted targets did not become UP with a fresh scrape")
    record["baseline_scrapes_utc"] = scrape_record(scrapes)
    record["lookback_started_at"] = utc()
    atomic_json(args.record, record)
    time.sleep(args.lookback)
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        scrapes = fresh_scrapes(args.prometheus, expected)
        if expected <= scrapes.keys():
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("allowlisted targets are not UP after lookback")
    verify_manifest(args, record)
    record["lookback_finished_at"] = utc()
    record["post_lookback_scrapes_utc"] = scrape_record(scrapes)
    atomic_json(args.record, record)


def finish(args):
    record = read(args.record)
    verify_manifest(args, record)
    expected = set(record["services"])
    drained = datetime.fromisoformat(args.drain_end.replace("Z", "+00:00"))
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        scrapes = fresh_scrapes(args.prometheus, expected, drained)
        if expected <= scrapes.keys():
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("final scrape missing for one or more allowlisted targets")
    record["status"] = "final_scrape_recorded"
    record["load_started_at"] = args.load_start
    record["load_ended_at"] = args.load_end
    record["generator_drained_at"] = args.drain_end
    record["final_scrapes_utc"] = scrape_record(scrapes)
    from_ms = round(datetime.fromisoformat(args.load_start.replace("Z", "+00:00")).timestamp() * 1000)
    to_ms = round(datetime.fromisoformat(args.load_end.replace("Z", "+00:00")).timestamp() * 1000)
    record["grafana_url"] = ("http://127.0.0.1:13000/d/project3-monitoring-demo/f67e2fb?" + urlencode({
        "var-job": "project3-console-run", "var-rate_window": "4s", "from": from_ms, "to": to_ms}))
    atomic_json(args.record, record)
    verify_manifest(args, record)
    args.path.unlink()
    record["status"] = "complete"
    record["deregistered_at"] = utc()
    atomic_json(args.record, record)


def remove(args):
    if not args.record.exists():
        return
    record = read(args.record)
    if record.get("owner") != args.owner:
        return
    if args.path.exists():
        if read(args.path) != record.get("targets"):
            return
        args.path.unlink()
    if record.get("status") != "complete":
        record["status"] = "incomplete"
        record["deregistered_at"] = utc()
        atomic_json(args.record, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "wait", "finish", "remove"))
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--instances", type=int, choices=(1, 2, 4))
    parser.add_argument("--prometheus", default="http://127.0.0.1:19090")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--lookback", type=float, default=4)
    parser.add_argument("--load-start")
    parser.add_argument("--load-end")
    parser.add_argument("--drain-end")
    args = parser.parse_args()
    try:
        {"register": register, "wait": wait_for_targets, "finish": finish, "remove": remove}[args.action](args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"console-monitoring: {exc}\n")


if __name__ == "__main__":
    main()
