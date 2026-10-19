# T07 outage runner preparation

This package prepares `scripts/redis-outage.sh` for a bounded live calibration after the shared-host LOAD BATON is granted. It does not contain live outage measurements.

For each fail policy, the runner saves a healthy 25-second baseline, computes and records `1.5 ×` its legitimate successful-request p95, then uses that threshold for the matching Redis-pause case. Both phases use the same policy, load, backend, two-API topology, and isolated run namespace. Each outage case records requested/completed pause transitions, policy, resolved Compose JSON, per-service before/after counters, image inspect data, source revision/status, generator evidence, and analyzer output. It saves to a new output directory and uses a unique Compose project; cleanup attempts to unpause Redis before removing only that project.

Focused preparation checks: `python3 -m unittest -v scripts.test_redis_outage`, `bash -n scripts/redis-outage.sh`, Python compilation of the existing topology renderer and analyzer, and `git diff --check` passed. The outage test mocks every Docker and load-generator command; it checks matched policy/topology inputs, complete per-service artifacts, all four transition events, healthy-derived threshold availability before outage load starts, output collision rejection, and unpause/down cleanup after a simulated pause failure. Live calibration is limited to the separate authorized T07 run below.

Known bound: the candidate requires at least five successful legitimate healthy samples, five seconds after the requested pause interval, and integer duration/rate/pause settings. Control-plane delay consumes the available post-outage offered-load period; analyzer marks recovery inconclusive if there are not three complete clean windows.
## Initial live attempt

The first attempt used clean revision `aa16cb0e372b4e1d3520b58514c479842e41df2f` and stopped during the cold Compose build before any workload started. The runner wrapped `up --wait --wait-timeout 120` in an outer 10-second timeout; Compose was killed while building the API image. The unique project left no containers (`docker ps -a` was empty for the check). The partial policy/resolved Compose/build output, fresh pre-load observer, config, tool hashes, and checksums are preserved in [`attempt-aa16cb0-build-timeout-evidence.tar.gz`](attempt-aa16cb0-build-timeout-evidence.tar.gz), SHA-256 in the adjacent `.sha256` file.

A minimal correction extends only the bounded outer `up` timeout to 180 seconds. The mocked lifecycle check now asserts all four phase starts use that outer bound; both test cases, shell syntax, and `git diff --check` passed after the change. No retry is authorized until the correction is integrated at a new clean revision.
