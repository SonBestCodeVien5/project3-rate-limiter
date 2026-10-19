#!/usr/bin/env python3
"""Mock the outage runner lifecycle; never starts Docker or real load."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/redis-outage.sh"
REAL_PYTHON = os.environ.get("PYTHON", shutil.which("python3"))


class RedisOutageRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands.log"
        self._script("timeout", """#!/bin/bash
echo "timeout $*" >>"$MOCK_LOG"
shift
if [[ $1 == */loadgen ]]; then
  shift
  while (($#)); do if [[ $1 == -out ]]; then dir=$2; shift 2; else shift; fi; done
  mkdir -p "$dir"
  if [[ $dir == */outage/load ]]; then
    if [[ -s "$(dirname "$(dirname "$dir")")/recovery-p95-threshold-ms.txt" ]]; then echo threshold-present >"$(dirname "$dir")/threshold-at-load-start.txt"; else echo threshold-missing >"$(dirname "$dir")/threshold-at-load-start.txt"; fi
  fi
  printf '{"config":{"duration_ns":25000000000}}\\n' >"$dir/metadata.json"
printf '{"scheduled":5,"sent":5,"generator_dropped":0,"canceled":false,"run_id":"open-healthy"}\\n' >"$dir/summary.json"
  printf '{"scheduled":5,"sent":5,"generator_dropped":0,"canceled":false,"run_id":"open-healthy"}\\n' >"$dir/summary.json"
  for i in 1 2 3 4 5; do printf '{"client_class":"legitimate","sent_at":"2026-10-19T00:00:00Z","status":200,"latency_ms":10}\\n' >>"$dir/requests.jsonl"; done
  exit 0
fi
exec "$@"
""")
        self._script("sleep", "exit 0\n")
        self._script("go", """#!/bin/bash
while (($#)); do if [[ $1 == -o ]]; then out=$2; shift 2; else shift; fi; done
cat >"$out" <<'LOAD'
#!/bin/bash
while (($#)); do if [[ $1 == -out ]]; then dir=$2; shift 2; else shift; fi; done
mkdir -p "$dir"
if [[ $dir == */outage/load ]]; then
  if [[ -s "$(dirname "$(dirname "$dir")")/recovery-p95-threshold-ms.txt" ]]; then echo threshold-present >"$(dirname "$dir")/threshold-at-load-start.txt"; else echo threshold-missing >"$(dirname "$dir")/threshold-at-load-start.txt"; fi
fi
printf '{"config":{"duration_ns":25000000000}}\\n' >"$dir/metadata.json"
for i in 1 2 3 4 5; do printf '{"client_class":"legitimate","sent_at":"2026-10-19T00:00:00Z","status":200,"latency_ms":10}\\n' >>"$dir/requests.jsonl"; done
LOAD
chmod +x "$out"
""")
        self._script("docker", """#!/bin/bash
echo "docker $*" >>"$MOCK_LOG"
if [[ $1 == compose ]]; then
  shift
  while (($#)); do case $1 in -f|-p|--project-directory) shift 2;; *) break;; esac; done
  case ${1:-} in
    version) exit 0;;
    config) cat <<JSON
{"services":{"api1":{"environment":{"MODE":"$MODE","ALGORITHM":"$ALGORITHM","FAIL_POLICY":"$FAIL_POLICY","NAMESPACE":"$NAMESPACE","LIMIT":"$LIMIT","WINDOW":"$WINDOW","CAPACITY":"$CAPACITY","RATE":"$RATE"}},"api2":{},"backend":{},"redis":{},"nginx":{}}}
JSON
      ;;
    images) echo '[{"ID":"sha256:mock"}]';;
    ps) exit 0;;
    exec) n=0; [[ ! -f "$MOCK_LOG.count" ]] || n=$(cat "$MOCK_LOG.count"); n=$((n+1)); echo "$n" >"$MOCK_LOG.count"; if [[ ${MOCK_BACKEND_OVERLOAD:-0} == 1 && $* == *backend* ]] && (( n == 4 )); then printf '{"overload":1,"limiter_errors":0}\\n'; else printf '{"overload":0,"limiter_errors":0}\\n'; fi;;
    up) if [[ ${MOCK_FAIL_UP:-0} == 1 ]]; then echo partial-created >>"$MOCK_LOG"; exit 1; fi; exit 0;;
    pause) if [[ ${MOCK_FAIL_PAUSE:-0} == 1 ]]; then exit 1; fi; exit 0;;
    *) exit 0;;
  esac
elif [[ $1 == info || $1 == version || $1 == ps ]]; then
  [[ $1 != ps ]] || exit 0
elif [[ $1 == image && $2 == inspect ]]; then
  if [[ $3 == --format ]]; then echo '[] sha256:mock'; else echo '[{"Id":"sha256:mock"}]'; fi
fi
""")
        self._script("python3", f"""#!/bin/bash
for arg in \"$@\"; do
  if [[ $arg == */scripts/analyze.py ]]; then echo \"analyze $*\" >>\"$MOCK_LOG\"; exit 0; fi
done
exec {REAL_PYTHON} \"$@\"
""")
        self.env = os.environ | {
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "MOCK_LOG": str(self.log),
            "OUTAGE_DURATION": "8", "OUTAGE_PAUSE_AT": "1", "OUTAGE_PAUSE_FOR": "1",
            "OUTAGE_RPS": "10", "OUTAGE_LEGIT_RPS": "5",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def _script(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
        path.chmod(0o755)

    def _run(self, output, **extra):
        return subprocess.run(["bash", str(RUNNER), str(output)], env=self.env | extra,
                              text=True, capture_output=True, timeout=20)

    def test_artifacts_matching_threshold_events_and_no_overwrite(self):
        out = self.root / "out"
        run = self._run(out)
        detail = self.log.read_text() if self.log.exists() else ""
        for artifact in out.rglob("*") if out.exists() else ():
            if artifact.is_file() and artifact.name.endswith(".log"):
                detail += f"\n{artifact}: {artifact.read_text(errors='replace')}"
        self.assertEqual(run.returncode, 0, run.stdout + "\n" + run.stderr + "\n" + detail)
        commands = self.log.read_text()
        timeout_commands = [line for line in commands.splitlines() if line.startswith("timeout ")]
        self.assertEqual(sum(line.startswith("timeout 180s docker compose ") and " up " in line for line in timeout_commands), 4)
        for policy in ("open", "closed"):
            healthy, outage = out / policy / "healthy", out / policy / "outage"
            hp, op = json.loads((healthy / "policy.json").read_text()), json.loads((outage / "policy.json").read_text())
            self.assertEqual({k: hp[k] for k in ("mode", "algorithm", "fail_policy", "limit", "window_ms", "capacity", "rate_per_sec")},
                             {k: op[k] for k in ("mode", "algorithm", "fail_policy", "limit", "window_ms", "capacity", "rate_per_sec")})
            self.assertNotEqual(hp["namespace"], op["namespace"])
            for case in (healthy, outage):
                for artifact in ("compose-resolved.json", "image-inspect.json", "backend-before.json", "backend-after.json", "api1-before.json", "api1-after.json", "api2-before.json", "api2-after.json", "load/metadata.json", "load/requests.jsonl"):
                    self.assertTrue((case / artifact).is_file(), f"missing {case / artifact}")
            expected = {"pause_requested", "pause_completed", "unpause_requested", "unpause_completed"}
            events = [line.split()[-1] for line in (outage / "outage-events.txt").read_text().splitlines()
                      if line.strip() and line.split()[-1] in expected]
            self.assertEqual(events, ["pause_requested", "pause_completed", "unpause_requested", "unpause_completed"])
            threshold = float((out / policy / "recovery-p95-threshold-ms.txt").read_text())
            self.assertEqual(threshold, 15.0)
            self.assertEqual((outage / "threshold-at-load-start.txt").read_text().strip(), "threshold-present")
            self.assertIn("--recovery-p95-ms 15", commands)
        docker_commands = [line for line in commands.splitlines() if line.startswith("docker ")]
        self.assertEqual(sum(" pause redis" in line for line in docker_commands), 2)
        self.assertEqual(sum(" unpause redis" in line for line in docker_commands), 2)
        again = self._run(out)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("Output already exists", again.stderr)

    def test_pause_failure_unpauses_and_removes_owned_project(self):
        out = self.root / "failed"
        run = self._run(out, MOCK_FAIL_PAUSE="1")
        self.assertNotEqual(run.returncode, 0)
        commands = self.log.read_text()
        self.assertIn("pause redis", commands)
        self.assertIn("unpause redis", commands)
        self.assertIn("down --remove-orphans", commands)


    def test_partial_up_failure_removes_owned_project(self):
        out = self.root / "partial-up"
        run = self._run(out, MOCK_FAIL_UP="1")
        self.assertNotEqual(run.returncode, 0)
        commands = self.log.read_text()
        self.assertIn("partial-created", commands)
        compose_commands = [line for line in commands.splitlines() if line.startswith("docker compose")]
        up = next(line for line in compose_commands if " up " in line)
        down = next(line for line in compose_commands if " down --remove-orphans" in line)
        project = up.split(" -p ", 1)[1].split()[0]
        self.assertIn(f"-p {project}", down)


    def test_unhealthy_healthy_baseline_stops_before_outage(self):
        out = self.root / "bad-baseline"
        run = self._run(out, MOCK_BACKEND_OVERLOAD="1")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("healthy baseline gate failed", run.stderr)
        self.assertTrue((out / "open/healthy/load/metadata.json").is_file())
        self.assertFalse((out / "open/outage").exists())


if __name__ == "__main__":
    unittest.main()
