# P2-05 technical closeout evidence

## Code and checks

- Focused fix commit: `c840a1edfd14f8b131551249e2b36eb2c9447c6f` (`fix(console): propagate cancel to research loadgen`). The existing runner now invokes loadgen with GNU `timeout --foreground`, keeping Console, runner, timeout and loadgen in the process group that Console cancels.
- Regression `TestResearchRunnerLoadgenSharesConsoleProcessGroup` reads the actual loadgen launch line from `scripts/research-pilot.sh`, requires `--foreground`, runs that extracted command with a bounded local fake child, and verifies group SIGTERM terminates both runner and child.
- Checks passed: `bash -n scripts/research-pilot.sh`; `git diff --check`; `GOCACHE=/tmp/p2-05-lifecycle-gocache go test ./internal/console`; `go test ./internal/experiment ./internal/server`; final `go test ./...` with loopback listener permission. The first sandboxed full-suite attempt failed only because the sandbox disallowed `httptest` loopback binds; the escalated rerun passed all packages.
- The test uses no network benchmark or Redis outage. T09/T10 sources and locked evidence were not changed.

## Console runner lifecycle

| Attempt | Run ID | Result |
|---|---|---|
| Normal UI run | `20261025T050941-8f78f2d67c87` | Passed: 600 scheduled/sent, all 600 HTTP 2xx, monitoring `complete`. Registration and fresh baseline/lookback preceded load. Generator drain was `05:10:38.025Z`; all three final scrapes were `05:10:38.565Z`. Exact Grafana bounds matched workload UTC `05:10:08.020Z–05:10:38.020Z`. |
| Cancel attempt 2 | `20261025T051659-d1cc11d15a14` | Cancel POST was issued during active load and returned 202, but generator completed all 600 requests/30 seconds (`canceled=false`). Root cause: GNU `timeout` default process-group isolation kept loadgen outside the Console-signaled group. This is preserved as the concrete failure that motivated `c840a1e`. |
| Attempt 3 | `20261025T052516-883b4d2fed22` | Completed a normal 600-request/30-second run after the fix, with monitoring `complete` and final scrapes after drain. It was not canceled because the observation sequence missed the active interval while waiting for setup; this is an orchestration miss, not a runner defect. |
| Cancel attempt 4 | `20261025T053020-e13041f1c4b5` | Passed active cancellation after the fix. The pre-armed browser watcher verified the exact form and new run ID, read Console metrics until API `/work` counters were positive (`api1=9`, `api2=16`), then synchronously clicked the existing `#cancel` button. The UI-issued POST returned 202. Loadgen reports `canceled=true`, 31 scheduled/sent, 30 HTTP 2xx and one transport error; it ended in 1.534 seconds against the 30-second duration. No 429, 5xx or timeout. Runner status is `canceled`; its owner record is `incomplete` and was deregistered at `05:30:45.161Z`. Cancellation has no post-cancel final scrape, as expected for an interrupted run. |

Actual scheduled requests across these four submissions: 1,831 (600 + 600 + 600 + 31). The four attempts are preserved; no fifth load attempt was made.

The regression proves process-group behavior with the actual runner command. The fourth Console run proves that the production cancellation path now interrupts the active generator. After completion, there were no research runner, loadgen or sampler processes, no active target manifest, and the research lock was free.

## Monitoring and telemetry

- Successful-run Prometheus queries and exact UTC workload interval are in `retained-prometheus-query.json`. The query ran after research cleanup and retained the three target series and workload samples; the final scrape was strictly after generator drain.
- Grafana dashboard/Explore were opened in the browser. The exact Explore URL is in `grafana-explore-after-success-url.txt`; selected screenshots are in `screenshots/`. The dashboard query returned HTTP 200 for its panels, and Explore returned the three API/backend startup JSON entries with no browser console errors.
- Loki startup entries were queried while the second workload was active (`during-cancel-log-query.json`); the same source/service type was queried over the completed normal run interval (`during-log-query.json`, after-success range `05:09:30Z–05:10:53.749Z`). Each query returned three parseable startup JSON entries for `api1`, `api2`, and `backend`. No claim is made that the fourth run's own startup logs were queried during cancellation; the watcher deliberately avoided all extra queries until after cancel.
- Prior G2 evidence in `../p2-05-runtime-20261025T041553Z/checks.md` covers startup/recovery log ingestion, all five research services (`api1…api4/backend`), opt-out absence, excluded-project negative control, stable labels, JSON parsing, source/Docker timestamp comparison, Prometheus scrape/query checks, and bounded Alloy/Loki restart behavior. Replay observations do not establish exactly-once delivery.
- JSON `/metrics` schema remained unchanged; the Console normal run records the before/after API and backend JSON metrics summary in `success-json-metrics-summary.json`.

## Registration and safety checks

- Lock contention refused before topology/load creation (run `20261025T050643-35adea68462d`).
- The owner-created stale target manifest was refused by the UI runner before workload (run `20261025T050806-863d39e474fd`). Wrong-owner removal left its fingerprint unchanged; matching-owner removal succeeded; a later legitimate registration succeeded. Evidence is under `stale-registration/`.
- Opt-out and excluded-project runtime evidence is in the prior G2 batch. No unrelated project/service appeared in the fixed/research stream label set; Redis, Nginx and monitoring services were excluded. The negative-control project was actually started with an opt-in label but was not discovered by the collector.
- Credentials were not printed, rotated or included in selected evidence. No raw Docker inspect environment, TSDB, Loki chunks or request trace was committed.

## Final resources, revisions and limitations

- Runtime code revision: `c840a1edfd14f8b131551249e2b36eb2c9447c6f`; the run metadata records only the generated browser directory and two generated Grafana screenshots as untracked at generator start. Root-owned documentation changes were already committed before this code fix.
- The nine original fixed demo container IDs were preserved; all are Exited with exit code 0 as initially observed. Four named volumes and two networks remain. The last stored health probes for services with healthchecks succeeded between `05:38:29Z` and `05:38:34Z`, before the containers stopped between `05:38:35.2Z` and `05:38:35.8Z`; Loki and Alloy have no Docker healthcheck. No containers, volumes or networks were removed.
- Current fixed resources are stopped to restore the initially observed state. Browser tabs and the Console process started by this session are closed. Generated `.playwright-mcp` outputs were moved intact under `browser-raw/`; selected screenshots were moved under `screenshots/`.
- The canceled run has no final scrape because the process group was interrupted. Normal-run metrics/log query evidence is complete. Startup logs do not promise one message per successful request or a graceful-shutdown message.
- Technical verification is complete for P2-05. Learner confirmation remains for the user. P2-06 is the next task only under its own scope and authorization gate; no P2-06/07/08 work was performed here.
