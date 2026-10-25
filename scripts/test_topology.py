#!/usr/bin/env python3
"""Small isolated renderer checks; no Docker daemon required."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name("render-topology.py")
spec = importlib.util.spec_from_file_location("render_topology", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RendererTest(unittest.TestCase):
    def setUp(self):
        self.base = {"name": "baseline", "services": {
            "api1": {"environment": {"INSTANCE_ID": "api-1", "MODE": "redis",
                                     "ALGORITHM": "fixed-window", "FAIL_POLICY": "closed",
                                     "NAMESPACE": "fresh", "LIMIT": "20", "WINDOW": "1s",
                                     "CAPACITY": "20", "RATE": "20"},
                     "ports": [{"published": "18081"}]},
            "api2": {"environment": {"INSTANCE_ID": "api-2"}},
            "backend": {"environment": {"BACKEND_CAPACITY": "10"}, "ports": [{"published": "18083"}]},
            "redis": {"ports": [{"published": "16379"}]},
            "nginx": {"ports": [{"published": "8080"}],
                      "depends_on": {"api1": {}, "api2": {}}}}}

    def test_one_two_four(self):
        for count in (1, 2, 4):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp:
                config, nginx, policy = module.render(self.base, count, Path(temp), 18080, True)
                services = config["services"]
                expected = {f"api{i}" for i in range(1, count + 1)}
                self.assertEqual({x for x in services if x.startswith("api")}, expected)
                self.assertEqual(set(services["nginx"]["depends_on"]), expected)
                self.assertEqual(nginx.count("server api"), count)
                self.assertNotIn(f"server api{count + 1}:8080", nginx)
                self.assertEqual(services["backend"]["environment"]["BACKEND_CAPACITY"], "10")
                self.assertNotIn("ports", services["backend"])
                self.assertNotIn("ports", services["redis"])
                self.assertTrue(all("ports" not in services[name] for name in expected))
                self.assertEqual(services["nginx"]["ports"][0]["host_ip"], "127.0.0.1")
                self.assertEqual(policy["window_ms"], 1000)
                self.assertTrue(policy["state_reset"])

    def test_monitoring_allowlist_for_one_two_four(self):
        for count in (1, 2, 4):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temp:
                config, _, _ = module.render(self.base, count, Path(temp), 18080, monitoring=True)
                self.assertEqual(config["networks"]["monitoring-scrape"],
                                 {"name": "project3-monitoring-scrape", "external": True})
                self.assertEqual(set(config["services"]), {"backend", "redis", "nginx", *(f"api{i}" for i in range(1, count + 1))})
                for i in range(1, count + 1):
                    self.assertIn(f"console-api{i}", config["services"][f"api{i}"]["networks"]["monitoring-scrape"]["aliases"])
                    self.assertEqual(config["services"][f"api{i}"]["labels"]["project3.monitoring.logs"], "true")
                self.assertEqual(config["services"]["backend"]["networks"]["monitoring-scrape"]["aliases"], ["console-backend"])
                self.assertEqual(config["services"]["backend"]["labels"]["project3.monitoring.logs"], "true")
                for name in ("redis", "nginx"):
                    self.assertNotIn("project3.monitoring.logs", config["services"][name].get("labels", {}))
                self.assertNotIn("monitoring-scrape", config["services"]["redis"].get("networks", {}))
                self.assertNotIn("monitoring-scrape", config["services"]["nginx"].get("networks", {}))

    def test_monitoring_log_opt_out_has_no_opt_in_labels(self):
        config, _, _ = module.render(self.base, 4, Path("/tmp"), 18080, monitoring=False)
        self.assertNotIn("labels", config["services"]["api1"])
        self.assertNotIn("labels", config["services"]["api2"])
        self.assertNotIn("project3.monitoring.logs", config["services"]["backend"].get("labels", {}))

    def test_invalid_count_and_no_unproved_reset(self):
        with tempfile.TemporaryDirectory() as temp:
            for count in (0, 3, 5):
                with self.assertRaises(ValueError):
                    module.render(self.base, count, Path(temp), 18080)
            _, _, policy = module.render(self.base, 2, Path(temp), 18080)
            self.assertFalse(policy["state_reset"])

    def test_cli_refuses_existing_output(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "base.json"
            base.write_text(json.dumps(self.base))
            output = Path(temp) / "topology"
            output.mkdir()
            marker = output / "do-not-overwrite"
            marker.write_text("safe")
            result = subprocess.run(["python3", str(SCRIPT), "--base-config", str(base),
                                     "--output", str(output), "--instances", "2"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), "safe")

    def test_fixed_monitoring_stack_keeps_apps_on_default_network(self):
        root = SCRIPT.parent.parent
        with tempfile.TemporaryDirectory() as temp:
            secret = Path(temp) / "grafana-password"
            secret.write_text("test-only")
            env = {**os.environ, "GRAFANA_ADMIN_PASSWORD_FILE": str(secret)}
            result = subprocess.run([
                "docker", "compose", "-p", "project3-monitoring-test",
                "-f", str(root / "compose.yaml"), "-f", str(root / "compose.observability.yaml"),
                "config", "--format", "json",
            ], cwd=root, env=env, check=True, capture_output=True, text=True)
        services = json.loads(result.stdout)["services"]
        for name in ("api1", "api2", "backend", "redis", "nginx"):
            self.assertIn("default", services[name]["networks"])
        for name, alias in (("api1", "fixed-api1"), ("api2", "fixed-api2"),
                            ("backend", "fixed-backend")):
            self.assertEqual(set(services[name]["networks"]), {"default"})
            self.assertIn(alias, services[name]["networks"]["default"]["aliases"])
        self.assertEqual(set(services["prometheus"]["networks"]), {"default", "monitoring-scrape"})


if __name__ == "__main__":
    unittest.main()
