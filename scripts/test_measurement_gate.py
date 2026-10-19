import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MeasurementGateTest(unittest.TestCase):
    def test_observer_detects_wall_step(self):
        observer = load("observer", ROOT / "scripts/observe-clock.py")
        rows = [{"wall_ns": 0, "monotonic_ns": 0}, {"wall_ns": 6_000_001, "monotonic_ns": 1}]
        self.assertEqual(observer.clock_steps(rows)[0]["difference_ms"], 6)
        self.assertEqual(observer.clock_steps([{"wall_ns": 0, "monotonic_ns": 0}, {"wall_ns": 6_000_000, "monotonic_ns": 1_000_000}]), [])

    def test_checker_error_is_saved_and_nonzero(self):
        checker = load("checker", ROOT / "scripts/check-gate-quality.py")
        with tempfile.TemporaryDirectory() as td:
            case = pathlib.Path(td)
            result = checker.check(case)
            self.assertFalse(result["valid"])
            self.assertIn("checker_error", json.loads((case / "quality.json").read_text())["flags"])

    def test_gate_stops_after_same_checker_blocker_across_profiles(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("run-measurement-gate.sh", "check-gate-quality.py"):
                (scripts / name).write_bytes((ROOT / "scripts" / name).read_bytes())
            (scripts / "fake-runner").write_text("#!/usr/bin/env bash\nout=\"${@: -1}\"; mkdir -p \"$out/custom-repeat-1\"\n")
            (scripts / "fake-runner").chmod(0o755)
            out = root / "gate"
            run = subprocess.run(["bash", str(scripts / "run-measurement-gate.sh"), "--output-root", str(out), "--runner", str(scripts / "fake-runner")], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertTrue((out / "normal-1/output/custom-repeat-1/quality.json").exists())
            self.assertTrue((out / "normal-2/output/custom-repeat-1/quality.json").exists())
            self.assertFalse((out / "normal-3").exists())

    def test_runner_failure_and_output_reuse_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "run-measurement-gate.sh").write_bytes((ROOT / "scripts/run-measurement-gate.sh").read_bytes())
            fail = scripts / "fail-runner"
            fail.write_text("#!/bin/sh\nexit 23\n")
            fail.chmod(0o755)
            out = root / "gate"
            cmd = ["bash", str(scripts / "run-measurement-gate.sh"), "--output-root", str(out), "--runner", str(fail)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads((out / "normal-1/runner-failure.json").read_text())["runner_status"], 23)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
