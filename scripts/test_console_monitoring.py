#!/usr/bin/env python3
"""Focused file_sd lifecycle checks; uses only temporary files and a mock Prometheus API."""

import importlib.util
import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch
import unittest

SCRIPT = Path(__file__).with_name("console-monitoring.py")
spec = importlib.util.spec_from_file_location("console_monitoring", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConsoleMonitoringTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "active.json"
        self.record = self.root / "case" / "monitoring.json"

    def tearDown(self):
        self.tmp.cleanup()

    def register(self, owner="run1", instances=2):
        args = type("Args", (), {"path": self.path, "record": self.record,
                                  "owner": owner, "instances": instances,
                                  "prometheus": "mock://prometheus", "timeout": 0})()
        with patch.object(module, "query", return_value=[]):
            module.register(args)

    def test_stale_manifest_refuses_overwrite(self):
        self.path.write_text('[{"stale":true}]')
        with self.assertRaisesRegex(RuntimeError, "stale or active"):
            self.register()
        self.assertEqual(json.loads(self.path.read_text()), [{"stale": True}])

    def test_previous_scrape_series_block_registration(self):
        args = type("Args", (), {"path": self.path, "record": self.record, "owner": "run1",
                                  "instances": 2, "prometheus": "mock://prometheus", "timeout": 0})()
        with patch.object(module, "query", return_value=[{"metric": {"service": "api1"}}]):
            with self.assertRaisesRegex(RuntimeError, "previous Console scrape series"):
                module.register(args)
        self.assertFalse(self.path.exists())

    def test_cancel_or_failure_removes_only_owned_registration(self):
        self.register()
        module.remove(type("Args", (), {"path": self.path, "record": self.record, "owner": "run1"})())
        self.assertFalse(self.path.exists())
        self.assertTrue(self.record.exists())
        self.assertEqual(json.loads(self.record.read_text())["status"], "incomplete")
        self.register("run2")
        module.remove(type("Args", (), {"path": self.path, "record": self.record, "owner": "wrong"})())
        self.assertTrue(self.path.exists())
        self.assertEqual(json.loads(self.record.read_text())["owner"], "run2")

    def test_final_scrape_keeps_exact_load_bounds_and_url_then_deregisters(self):
        self.register()
        start, end = "2026-10-24T01:02:03.123Z", "2026-10-24T01:02:33.456Z"
        args = type("Args", (), {"path": self.path, "record": self.record, "owner": "run1",
                                  "prometheus": "mock://prometheus",
                                  "timeout": 1, "load_start": start, "load_end": end,
                                  "drain_end": "2026-10-24T01:02:34.111Z"})()
        stamps = [{"metric": {"service": service}, "value": ["now", str(time.time())]}
                  for service in ("api1", "api2", "backend")]
        with patch.object(module, "query", return_value=stamps):
            module.finish(args)
        data = json.loads(self.record.read_text())
        self.assertEqual(data["status"], "complete")
        self.assertIn("deregistered_at", data)
        self.assertEqual(data["load_started_at"], start)
        self.assertEqual(data["load_ended_at"], end)
        self.assertEqual(data["generator_drained_at"], "2026-10-24T01:02:34.111Z")
        self.assertIn("var-job=project3-console-run", data["grafana_url"])
        from urllib.parse import parse_qs, urlparse
        query = parse_qs(urlparse(data["grafana_url"]).query)
        self.assertEqual(query["from"], ["1792803723123"])
        self.assertEqual(query["to"], ["1792803753456"])
        self.assertEqual(query["var-rate_window"], ["4s"])
        self.assertFalse(self.path.exists())

    def test_baseline_and_lookback_are_recorded(self):
        self.register()
        stamps = [{"metric": {"service": service}, "value": ["now", str(time.time())]}
                  for service in ("api1", "api2", "backend")]
        args = type("Args", (), {"path": self.path, "record": self.record, "owner": "run1",
                                  "prometheus": "mock://prometheus", "timeout": 1, "lookback": 4})()
        with patch.object(module, "query", return_value=stamps), patch.object(module.time, "sleep") as sleep:
            module.wait_for_targets(args)
        record = json.loads(self.record.read_text())
        self.assertEqual(set(record["baseline_scrapes_utc"]), {"api1", "api2", "backend"})
        self.assertIn("lookback_started_at", record)
        self.assertIn("lookback_finished_at", record)
        sleep.assert_called_once_with(4)


if __name__ == "__main__":
    unittest.main()
