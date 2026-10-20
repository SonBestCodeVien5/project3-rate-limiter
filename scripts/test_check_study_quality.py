import importlib.util
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("checker", Path(__file__).with_name("check-study-quality.py"))
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
BASE = datetime(2026, 10, 20, tzinfo=timezone.utc)
REDIS = "sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952"
NGINX = "sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284"


class StudyQualityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture_number = 0

    def fixture(self, outage=False, outage_phase="outage"):
        self.fixture_number += 1
        case = self.root / f'{"outage" if outage else "standard"}-{self.fixture_number}'
        (case / "load").mkdir(parents=True)
        (case / "topology").mkdir()
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        (case / "git-revision.txt").write_text(revision + "\n")
        (case / "git-status.txt").write_text("\n")
        policy = dict(schema_version=1, mode="redis", algorithm="fixed-window", fail_policy="open" if outage else "closed",
                      namespace="test-ns", limit=100, window_ms=1000, capacity=100, rate_per_sec=100, state_reset=True)
        w = dict(legitimate_clients=5, duration_s=1, max_inflight=200, timeout_ms=2000, max_schedule_lag_ms=100,
                 profile="outage-pair" if outage else "normal", rps=100 if outage else 20,
                 legitimate_rps=20 if outage else 20, abusive_rps=80 if outage else 0)
        plan = dict(planned_run_id="planned", cell=f"outage-open-{outage_phase}" if outage else "normal-redis",
                    source_revision=revision, config=dict(policy=policy, workload=w,
                    topology=dict(api_instances=2, backend_capacity=10, backend_service_ms=50)))
        manifest = self.root / f'manifest-{self.fixture_number}.json'
        manifest.write_text(json.dumps(dict(runs=[plan])))
        config = dict(run_id="runtime", profile="mixed" if outage else "normal", duration_ns=1_000_000_000,
                      rps=w["rps"], legitimate_rps=w["legitimate_rps"], legitimate_clients=5, max_inflight=200,
                      timeout_ns=2_000_000_000, max_schedule_lag_ns=100_000_000,
                      mode_label="redis", algorithm_label="fixed-window", fail_policy_label=policy["fail_policy"])
        metadata = dict(config=config, git_revision=revision, git_status_porcelain="")
        summary = dict(run_id="runtime", started_at=BASE.isoformat(), ended_at=(BASE+timedelta(seconds=1)).isoformat(),
                       scheduled=100 if outage else 20, sent=100 if outage else 20, generator_dropped=0,
                       http_429=0, backend_confirmed_arrivals=100 if outage else 20, legitimate_successful=20,
                       transport_errors=0, timeouts=0, canceled=False)
        rows = []
        for i in range(summary["sent"]):
            klass = "legitimate" if i < (20 if outage else 20) else "abusive"
            t = i * (10 if outage else 50)
            scheduled = BASE + timedelta(milliseconds=t)
            sent = scheduled + timedelta(milliseconds=1)
            rows.append(dict(request_id=str(i), client_class=klass, scheduled_at=scheduled.isoformat(),
                             sent_at=sent.isoformat(), end_at=(sent+timedelta(milliseconds=5)).isoformat(),
                             schedule_lag_ms=1, latency_ms=5, status=200, timeout=False, limiter_decision="allow"))
        (case / "load/metadata.json").write_text(json.dumps(metadata))
        (case / "load/summary.json").write_text(json.dumps(summary))
        (case / "load/requests.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        (case / "policy.json").write_text(json.dumps(policy))
        (case / "topology/policy.json").write_text(json.dumps(policy))
        env = dict(MODE="redis", ALGORITHM="fixed-window", FAIL_POLICY=policy["fail_policy"], LIMIT="100",
                   WINDOW="1s", CAPACITY="100", RATE="100", NAMESPACE="test-ns")
        services = {f"api{i}": dict(environment=env) for i in (1, 2)}
        services.update(backend=dict(environment=dict(BACKEND_CAPACITY="10", BACKEND_SERVICE_TIME="50ms")), redis=dict(image="redis:7.4.2-alpine"), nginx=dict(image="nginx:1.28.0-alpine"))
        (case / "compose-resolved.json").write_text(json.dumps(dict(services=services)))
        tags = dict(redis="7.4.2-alpine", nginx="1.28.0-alpine")
        image_rows, inspect_rows = [], []
        for n in ("api1", "api2", "backend", "redis", "nginx"):
            image_id = "id-"+n
            image_rows.append(dict(ContainerName="project-run-"+n+"-1", ID=image_id, Platform="linux/amd64", Tag=tags.get(n,"latest")))
            inspect_rows.append(dict(Id=image_id, RootFS=dict(Layers=["sha256:"+"a"*64]), Config=dict(Env=["X=1"])))
        (case / "images.json").write_text(json.dumps(image_rows))
        (case / "image-inspect.json").write_text(json.dumps(inspect_rows))
        (case / "base-image-digests.txt").write_text(REDIS+"\n"+NGINX+"\n")
        api = {f"api{i}": dict(requests=summary["sent"]//2, rejected=0, limiter_errors=0) for i in (1, 2)}
        if outage and plan["cell"].endswith("outage"):
            for item in api.values(): item["limiter_errors"] = 3
        analysis = dict(run_id="runtime", evidence=dict(summary_counts_match_trace=True), oracle=dict(status="inconclusive"),
                        counter_deltas={**api, "backend": dict(arrivals=summary["sent"], success=summary["sent"], overload=0, canceled=0)},
                        outage={"phases": {}} if outage and outage_phase == "outage" else None, redis_resources={"status":"incomplete"})
        (case / "analysis.json").write_text(json.dumps(analysis))
        if outage and outage_phase == "outage":
            (case / "outage-events.txt").write_text("\n".join(f"{(BASE+timedelta(seconds=s)).isoformat()} {n}" for s,n in zip((.4,.41,.6,.61),("pause_requested","pause_completed","unpause_requested","unpause_completed")))+"\n")
        return manifest, case

    def run_check(self, outage=False):
        manifest, case = self.fixture(outage)
        return checker.check(manifest, "planned", case), manifest, case

    def test_realistic_standard_and_outage_fixtures_pass_nullable_resources_and_inconclusive_oracle(self):
        for outage in (False, True):
            result, _, _ = self.run_check(outage)
            self.assertTrue(result["valid"], result["reasons"])
            self.assertEqual(result["oracle_status"], "inconclusive")

    def test_drops_phase_rate_and_lag_rejected(self):
        result, manifest, case = self.run_check()
        summary = json.loads((case/"load/summary.json").read_text()); summary["generator_dropped"] = 1; (case/"load/summary.json").write_text(json.dumps(summary))
        self.assertIn("generator_drops", checker.check(manifest, "planned", case)["reasons"])
        manifest, case = self.fixture()
        rows = [json.loads(x) for x in (case/"load/requests.jsonl").read_text().splitlines()]
        rows.pop(); (case/"load/requests.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        result = checker.check(manifest, "planned", case)
        self.assertTrue(any("rate_fidelity" in x for x in result["reasons"]))
        manifest, case = self.fixture()
        rows = [json.loads(x) for x in (case/"load/requests.jsonl").read_text().splitlines()]
        for row in rows: row["schedule_lag_ms"] = 51
        (case/"load/requests.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        self.assertTrue(any("schedule_lag" in x for x in checker.check(manifest, "planned", case)["reasons"]))

    def test_burst_phase_rates_and_both_clock_residuals(self):
        manifest, case = self.fixture()
        m = json.loads(manifest.read_text()); m["runs"][0]["config"]["workload"].update(profile="burst", duration_s=6, rps=40, legitimate_rps=20, abusive_base_rps=20, abusive_peak_rps=200, peak_start_s=2, peak_end_s=4); manifest.write_text(json.dumps(m))
        c = json.loads((case/"load/metadata.json").read_text())["config"]; c.update(profile="burst",rps=40,duration_ns=6_000_000_000,burst_start_ns=2_000_000_000,burst_duration_ns=2_000_000_000,burst_rps=200); (case/"load/metadata.json").write_text(json.dumps(dict(config=c,git_revision=m["runs"][0]["source_revision"],git_status_porcelain="")))
        result = checker.check(manifest,"planned",case)
        self.assertTrue(any("rate_fidelity:abusive:2-4" in x for x in result["reasons"]))
        manifest, case = self.fixture()
        rows=[json.loads(x) for x in (case/"load/requests.jsonl").read_text().splitlines()]; rows[0]["end_at"]=(BASE+timedelta(seconds=1)).isoformat(); (case/"load/requests.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        result=checker.check(manifest,"planned",case); self.assertIn("client_clock_residual",result["reasons"]); self.assertTrue(result["stop_sequence"])

    def test_scheduling_clock_residual_and_api_reconciliation(self):
        manifest, case = self.fixture()
        rows = [json.loads(x) for x in (case/"load/requests.jsonl").read_text().splitlines()]
        rows[0]["sent_at"] = (BASE+timedelta(milliseconds=20)).isoformat()
        (case/"load/requests.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        result = checker.check(manifest, "planned", case)
        self.assertIn("client_clock_residual", result["reasons"])
        self.assertTrue(result["stop_sequence"])
        manifest, case = self.fixture()
        a = json.loads((case/"analysis.json").read_text()); a["counter_deltas"]["api1"]["requests"] += 1
        (case/"analysis.json").write_text(json.dumps(a))
        self.assertIn("api_counter_reconciliation", checker.check(manifest, "planned", case)["reasons"])

    def test_config_topology_counter_and_outage_event_rejections(self):
        manifest, case=self.fixture(); p=json.loads((case/"compose-resolved.json").read_text()); p["services"]["api1"]["environment"]["MODE"]="local"; (case/"compose-resolved.json").write_text(json.dumps(p))
        self.assertTrue(any("topology_policy_mismatch" in x for x in checker.check(manifest,"planned",case)["reasons"]))
        manifest, case=self.fixture(); a=json.loads((case/"analysis.json").read_text()); a["counter_deltas"]["backend"]["success"]-=1; (case/"analysis.json").write_text(json.dumps(a))
        self.assertIn("backend_counter_reconciliation",checker.check(manifest,"planned",case)["reasons"])
        manifest, case=self.fixture(True); (case/"outage-events.txt").write_text("bad\n")
        self.assertIn("outage_event_order",checker.check(manifest,"planned",case)["reasons"])

    def test_interleaved_compose_output_is_ignored_but_event_order_remains_strict(self):
        manifest, case = self.fixture(True)
        event_file = case/"outage-events.txt"
        event_file.write_text(event_file.read_text().replace("\n", "\n Container redis-1 Paused \n", 1))
        result = checker.check(manifest, "planned", case)
        self.assertNotIn("outage_event_order", result["reasons"])
        event_file.write_text(event_file.read_text() + "2026-10-20T00:00:05Z pause_completed\n")
        self.assertIn("outage_event_order", checker.check(manifest, "planned", case)["reasons"])
        manifest, case = self.fixture(True)
        lines = (case/"outage-events.txt").read_text().splitlines()
        lines[0], lines[1] = lines[1], lines[0]
        (case/"outage-events.txt").write_text("\n".join(lines)+"\n")
        self.assertIn("outage_event_order", checker.check(manifest, "planned", case)["reasons"])

    def test_resolved_compose_pinned_image_tag_mismatch_stops_sequence(self):
        manifest, case = self.fixture()
        compose = json.loads((case/"compose-resolved.json").read_text())
        compose["services"]["redis"]["image"] = "redis:7.4-alpine"
        (case/"compose-resolved.json").write_text(json.dumps(compose))
        result = checker.check(manifest, "planned", case)
        self.assertIn("pinned_compose_image_mismatch:redis", result["reasons"])
        self.assertTrue(result["stop_sequence"])

    def test_expected_outage_limiter_errors_are_reported_but_healthy_errors_fail(self):
        result, _, _ = self.run_check(True)
        self.assertTrue(result["valid"], result["reasons"])
        self.assertEqual(result["limiter_errors"], 6)
        manifest, case = self.fixture()
        analysis = json.loads((case/"analysis.json").read_text())
        analysis["counter_deltas"]["api1"]["limiter_errors"] = 1
        (case/"analysis.json").write_text(json.dumps(analysis))
        self.assertIn("limiter_errors", checker.check(manifest, "planned", case)["reasons"])

    def test_healthy_outage_calibration_allows_null_analysis_outage_and_enforces_gate(self):
        manifest, case = self.fixture(outage=True, outage_phase="healthy")
        result = checker.check(manifest, "planned", case)
        self.assertTrue(result["valid"], result["reasons"])
        analysis = json.loads((case/"analysis.json").read_text())
        analysis["counter_deltas"]["api1"]["limiter_errors"] = 1
        (case/"analysis.json").write_text(json.dumps(analysis))
        self.assertIn("outage_healthy_gate", checker.check(manifest, "planned", case)["reasons"])

    def test_missing_expected_counter_key_with_extras_is_rejected(self):
        manifest, case = self.fixture()
        analysis = json.loads((case/"analysis.json").read_text())
        del analysis["counter_deltas"]["api1"]
        analysis["counter_deltas"]["api-extra"] = dict(requests=0, rejected=0, limiter_errors=0)
        (case/"analysis.json").write_text(json.dumps(analysis))
        self.assertIn("counter_evidence_missing", checker.check(manifest, "planned", case)["reasons"])

    def test_fingerprints_ignore_dynamic_container_names_and_malformed_artifacts_are_fatal_json(self):
        manifest, case = self.fixture()
        first = checker.check(manifest, "planned", case)
        images = json.loads((case/"images.json").read_text())
        for image in images: image["ContainerName"] = "another-random-project-" + image["ContainerName"].rsplit("-", 2)[-2] + "-1"
        (case/"images.json").write_text(json.dumps(images))
        second = checker.check(manifest, "planned", case)
        self.assertEqual(first["image_fingerprint"], second["image_fingerprint"])
        self.assertEqual(first["config_fingerprint"], second["config_fingerprint"])
        (case/"compose-resolved.json").write_text("{")
        fatal = checker.check(manifest, "planned", case)
        self.assertFalse(fatal["valid"])
        self.assertTrue(fatal["stop_sequence"])
        self.assertTrue(fatal["reasons"][0].startswith("fatal_artifact:"))

    def test_missing_and_malformed_artifacts_and_drop_reconciliation(self):
        manifest,case=self.fixture(); (case/"analysis.json").unlink()
        result=checker.check(manifest,"planned",case); self.assertTrue(result["stop_sequence"])
        manifest,case=self.fixture(); (case/"load/requests.jsonl").write_text("{bad\n")
        self.assertTrue(checker.check(manifest,"planned",case)["stop_sequence"])


if __name__ == "__main__":
    unittest.main()
