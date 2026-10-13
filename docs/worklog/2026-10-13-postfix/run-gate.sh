#!/usr/bin/env bash
set -u
export GOCACHE=/tmp/project3-review-go-cache CUSTOM_MODE=redis CUSTOM_ALGORITHM=fixed-window CUSTOM_INSTANCES=2 CUSTOM_DURATION=30 CUSTOM_LIMIT=20 CUSTOM_WINDOW_MS=1000 CUSTOM_CAPACITY=20 CUSTOM_RATE=20 CUSTOM_BACKEND_CAPACITY=4 CUSTOM_BACKEND_SERVICE_MS=50 CUSTOM_FAIL_POLICY=closed
for profile in normal mixed; do
 export CUSTOM_PROFILE=$profile CUSTOM_LEGIT_RPS=20
 if [[ $profile == normal ]];then export CUSTOM_RPS=20;else export CUSTOM_RPS=120;fi
 for repeat in 1 2 3;do
  label="$profile-$repeat"; output="artifacts/postfix-20261013/gate-$label"
  bash scripts/research-pilot.sh --case custom --repetitions 1 --analyze --output "$output" >"artifacts/postfix-20261013/gate-$label.log" 2>&1
  result=$?;echo "$label runner=$result"
  if ((result));then echo runner_failure > artifacts/postfix-20261013/GATE_STOP;exit 1;fi
  python3 /tmp/postfix-quality.py "$output/custom-repeat-1"
  python3 - <<'PY'
import json,pathlib,collections,sys
counter=collections.Counter(f for p in pathlib.Path('artifacts/postfix-20261013').glob('gate-*/custom-repeat-1/quality.json') for f in json.load(open(p))['flags'])
failed={k:v for k,v in counter.items() if v>=2}
if failed:pathlib.Path('artifacts/postfix-20261013/GATE_STOP').write_text(json.dumps(failed));sys.exit(2)
PY
  check=$?;if ((check));then exit "$check";fi
 done
done
echo complete > artifacts/postfix-20261013/GATE_COMPLETE
