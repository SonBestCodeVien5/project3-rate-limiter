#!/usr/bin/env python3
"""Observe wall/monotonic clock divergence into a fresh output directory."""
import argparse
import json
import pathlib
import time


def clock_steps(samples):
    steps = []
    for a, b in zip(samples, samples[1:]):
        wd, md = b["wall_ns"] - a["wall_ns"], b["monotonic_ns"] - a["monotonic_ns"]
        if abs(wd - md) > 5_000_000:
            steps.append({"wall_ns": b["wall_ns"], "wall_delta_ms": wd / 1e6,
                          "monotonic_delta_ms": md / 1e6, "difference_ms": (wd - md) / 1e6})
    return steps


def observe(output: pathlib.Path, duration: float) -> dict:
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    samples = []
    start = time.monotonic_ns()
    deadline = start + int(duration * 1e9)
    while True:
        m1 = time.monotonic_ns()
        wall = time.time_ns()
        m2 = time.monotonic_ns()
        samples.append({"wall_ns": wall, "monotonic_ns": (m1 + m2) // 2, "read_span_ns": m2 - m1})
        if m2 >= deadline:
            break
        time.sleep(min(.05, max(0, (deadline - m2) / 1e9)))
    steps = clock_steps(samples)
    info = {k: vars(time.get_clock_info(k)) for k in ("time", "monotonic")}
    summary = {"samples": len(samples), "elapsed_monotonic_seconds": (samples[-1]["monotonic_ns"] - samples[0]["monotonic_ns"]) / 1e9,
               "elapsed_wall_seconds": (samples[-1]["wall_ns"] - samples[0]["wall_ns"]) / 1e9,
               "clock_steps_above_5ms": steps, "max_read_span_us": max(s["read_span_ns"] for s in samples) / 1e3,
               "threshold_ms": 5, "duration_seconds": duration, "clock_info": info}
    (output / "samples.jsonl").write_text("".join(json.dumps(s) + "\n" for s in samples))
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps({"recorded_at_ns": time.time_ns(), "python": __import__("platform").python_version()}, indent=2) + "\n")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--duration-seconds", type=float, default=90)
    a = p.parse_args()
    if not 0 < a.duration_seconds <= 86400:
        p.error("duration must be in (0, 86400]")
    try:
        result = observe(a.output, a.duration_seconds)
    except (OSError, ValueError) as e:
        p.error(str(e))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
