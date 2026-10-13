import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

import analyze


BASE = datetime(2026, 10, 11, 0, 0, tzinfo=timezone.utc)


def at(ms):
    return (BASE + timedelta(milliseconds=ms)).isoformat()


def policy(**changes):
    result = dict(schema_version=1, mode="redis", algorithm="fixed-window", limit=2,
                  window_ms=1000, capacity=2, rate_per_sec=2, namespace="test", state_reset=True,
                  fail_policy="closed")
    result.update(changes)
    return result


def row(index, ms, decision="allow", instance="api1", klass="legitimate", sent=True, status=None):
    return dict(request_id=f"r{index}", client_key="k", client_class=klass, scheduled_at=at(ms),
                sent_at=at(ms) if sent else None, end_at=at(ms + 10), latency_ms=10,
                status=status if status is not None else (200 if decision in ("allow", "fail-open") else 429),
                timeout=False, limiter_decision=decision, decision_at=at(ms) if decision else None,
                instance=instance)


class AnalyzerTest(unittest.TestCase):
    def test_fixed_window_definite_overshoot_even_partial(self):
        result = analyze.oracle([row(i, 100 + i) for i in range(3)], policy())
        self.assertEqual(result["violations"][0]["observed_overshoot_lower_bound"], 1)
        self.assertFalse(result["violations"][0]["window_complete"])

    def test_fixed_window_fresh_partial_window_reject_detected(self):
        rows = [row(1, -100), row(2, 100, "reject"), row(3, 1100)]
        complete = analyze.oracle(rows, policy(), trace_complete=True)
        self.assertTrue(any(v["kind"] == "fixed_window_decision_mismatch" for v in complete["violations"]))
        self.assertTrue(all(not x["window_complete"] for x in complete["trace_decision_checks"]))
        partial = analyze.oracle(rows, policy(), trace_complete=False)
        self.assertFalse(partial["violations"])

    def test_fixed_window_valid_partial_trace_consistency(self):
        rows = [row(1, 100), row(2, 200), row(3, 300, "reject")]
        result = analyze.oracle(rows, policy(), trace_complete=True)
        self.assertFalse(result["violations"])
        self.assertEqual(result["trace_decision_checks"][0]["status"], "checked")
        self.assertFalse(result["trace_decision_checks"][0]["window_complete"])
        self.assertEqual(result["status"], "inconclusive")

    def test_canceled_run_disables_exact_replay(self):
        rows = [row(1, 100, "reject")]
        result = analyze.oracle(rows, policy(), trace_complete=True, run_canceled=True)
        self.assertFalse(result["violations"])
        self.assertEqual(result["trace_decision_checks"][0]["status"], "inconclusive")

    def test_local_instances_have_separate_quota_and_global_multiplication(self):
        rows = [row(1, 100, instance="api1"), row(2, 101, instance="api1"),
                row(3, 102, instance="api2"), row(4, 103, instance="api2")]
        result = analyze.oracle(rows, policy(mode="local"))
        self.assertFalse(result["violations"])
        self.assertEqual(result["observed_global_accepted_envelope"][0]["shared_quota_overshoot_lower_bound"], 2)

    def test_token_bucket_refill_exceeds_fixed_window_quota_validly(self):
        rows = [row(1, 0), row(2, 1), row(3, 500)]
        result = analyze.oracle(rows, policy(algorithm="token-bucket"), trace_complete=True)
        self.assertFalse(result["violations"])
        self.assertEqual(result["status"], "no_violation_observed_within_trace")

    def test_token_bucket_invalid_and_tied_timestamps(self):
        valid = analyze.oracle([row(1, 0), row(2, 0), row(3, 0, "reject")], policy(algorithm="token-bucket"), trace_complete=True)
        self.assertFalse(valid["violations"])
        invalid = analyze.oracle([row(1, 0), row(2, 0), row(3, 0)], policy(algorithm="token-bucket"), trace_complete=True)
        self.assertTrue(any(x["kind"] == "token_bucket_decision_mismatch" for x in invalid["violations"]))

    def test_token_bucket_all_rejects_has_empty_envelope(self):
        result = analyze.oracle([row(1, 0, "reject")], policy(algorithm="token-bucket"), trace_complete=True)
        self.assertEqual(result["observed_global_accepted_envelope"][0]["status"], "no_observed_allows")

    def test_token_bucket_exact_boundary_and_near_boundary(self):
        p = policy(mode="local", algorithm="token-bucket", capacity=1, rate_per_sec=20)
        rows = [row(0, 0), row(1, 3, "reject"), row(2, 32, "reject"), row(3, 50)]
        self.assertFalse(analyze.oracle(rows, p, trace_complete=True)["violations"])
        rows[-1] = row(3, 50, "reject")
        self.assertTrue(analyze.oracle(rows, p, trace_complete=True)["violations"])
        p["rate_per_sec"] = 999.99999995
        early = analyze.oracle([row(0, 0), row(1, 1)], p, trace_complete=True)
        self.assertEqual(early["violations"][-1]["expected_allows"], 0)
        valid = analyze.oracle([row(0, 0), row(1, 1, "reject")], p, trace_complete=True)
        self.assertFalse(valid["violations"])

    def test_all_generator_drops_cannot_pass_oracle(self):
        result = analyze.oracle([row(1, 0, sent=False)], policy(algorithm="token-bucket"), trace_complete=True)
        self.assertEqual(result["status"], "inconclusive")

    def test_missing_or_fallback_makes_replay_inconclusive(self):
        rows = [row(1, 0), row(2, 1, "fail-open"), row(3, 500)]
        result = analyze.oracle(rows, policy(algorithm="token-bucket"), trace_complete=True)
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(result["inconclusive_groups"])
        dropped = row(4, 700, sent=False)
        self.assertEqual(analyze.oracle([row(1, 0), dropped], policy(algorithm="token-bucket"), trace_complete=True)["status"], "no_violation_observed_within_trace")

    def test_outage_denominator_uses_sent_and_recovery_requires_evidence(self):
        base = BASE.timestamp()
        events = dict(zip(analyze.EVENTS, [base + x for x in (1, 2, 4, 5)]))
        rows = [row(1, 3000), row(2, 3100, "reject"), row(3, 3200, sent=False), row(4, 6000)]
        args = argparse.Namespace(recovery_window_ms=1000, recovery_min_samples=2, recovery_consecutive=2, recovery_p95_ms=100)
        out = analyze.outage_analysis(rows, events, args, measurement_end=base + 8)
        self.assertEqual(out["phases"]["outage"]["legitimate_availability"], .5)
        self.assertIsNone(out["recovery"]["stable_recovery_ms"])

    def test_stable_recovery_needs_two_clean_full_windows(self):
        base = BASE.timestamp()
        events = dict(zip(analyze.EVENTS, [base + x for x in (1, 2, 4, 5)]))
        rows = [row(1, 5100), row(2, 5200), row(3, 6100), row(4, 6200), row(5, 7200)]
        args = argparse.Namespace(recovery_window_ms=1000, recovery_min_samples=2, recovery_consecutive=2, recovery_p95_ms=100)
        out = analyze.outage_analysis(rows, events, args, measurement_end=base + 7.5)
        self.assertEqual(out["recovery"]["stable_recovery_ms"], 2000)

    def test_recovery_drain_does_not_complete_offered_window(self):
        base = BASE.timestamp()
        events = dict(zip(analyze.EVENTS, [base + x for x in (1, 2, 4, 5)]))
        rows = [row(1, 5100), row(2, 5200), row(3, 6100), row(4, 6200), row(5, 7200)]
        args = argparse.Namespace(recovery_window_ms=1000, recovery_min_samples=2, recovery_consecutive=2, recovery_p95_ms=100)
        out = analyze.outage_analysis(rows, events, args, measurement_end=base + 6.5)
        self.assertIsNone(out["recovery"]["stable_recovery_ms"])

    def test_optional_fields_and_snapshot_shape_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requests.jsonl"
            bad = row(1, 0)
            bad["instance"] = []
            path.write_text(json.dumps(bad) + "\n")
            with self.assertRaisesRegex(ValueError, "instance must be a string"):
                analyze.load_records(path)
            (Path(tmp) / "api1-before.json").write_text("[]")
            (Path(tmp) / "api1-after.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "counter snapshot must be JSON object"):
                analyze.counter_delta(Path(tmp))

    def test_invalid_policy_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(policy(state_reset="true")))
            with self.assertRaisesRegex(ValueError, "state_reset"):
                analyze.load_policy(path)

    def test_truncated_raw_trace_fails_summary_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            (case / "load").mkdir()
            (case / "policy.json").write_text(json.dumps(policy()))
            (case / "load/metadata.json").write_text(json.dumps({"config": {"run_id": "r"}}))
            (case / "load/summary.json").write_text(json.dumps({"run_id": "r", "scheduled": 2, "sent": 2, "generator_dropped": 0, "canceled": False}))
            (case / "load/requests.jsonl").write_text(json.dumps(row(1, 0)) + "\n")
            args = argparse.Namespace(recovery_window_ms=1000, recovery_min_samples=2, recovery_consecutive=2, recovery_p95_ms=None)
            with self.assertRaisesRegex(ValueError, "summary counts differ"):
                analyze.analyze(case, args)


if __name__ == "__main__":
    unittest.main()
