# Grafana dashboard-list UID collision fix

## Change and scope

Grafana 12.4.11 rendered the folder and its provisioned dashboard with the same UID, `project3-monitoring-demo`. The dashboard-list selection tree recursed by UID and did not guard cycles, causing the reported `RangeError: Maximum call stack size exceeded`. The provider now uses folder UID `project3-monitoring-folder` and title `Project 3 Monitoring`. Dashboard UID `project3-monitoring-demo`, datasource UID `project3-prometheus`, and the dashboard URL remain unchanged.

The update was applied to the user's running Grafana through `POST /api/admin/provisioning/dashboards/reload` (HTTP 200); no container was restarted. Grafana provisioned the existing dashboard into the new folder. The old `Project 3 Demo` folder remains present and empty; no folder, dashboard, alert, volume, or user data was deleted.

## Evidence bounds and source

- UTC diagnostic window: `2026-10-23T14:46:45.043537Z` through `2026-10-23T14:52:13.153122128Z`.
- Provisioning reload began at `2026-10-23T14:47:24.435407Z`; API state was captured at `2026-10-23T14:47:34.310707Z`.
- Chromium regression check completed at `2026-10-23T14:50:33.867310Z`.
- The reload used the provider content later committed as `9cecd15e49be3d0c5fcd93b5ccb0a94d6b8b4ff5`. The live provider bytes have SHA-256 `5cfd59e0bd9b6690e50d5fe21d5000658ae7d460a29a75862c171303800254e2` (see `provider.sha256`). At reload time, the same bytes were an uncommitted working-tree patch on parent `a7266fc2c744494396d5061385f4aee0a0f245af`; they are now committed unchanged.
- Actual Grafana version/API health reports `12.4.11`, commit `96836a94cb5e2e1e196bacd76edfa6d25673d4b4`; running image tag is `grafana/grafana:12.4.11`.

## Results

- Before reload, authenticated Grafana API returned one folder and one dashboard, both UID `project3-monitoring-demo`; dashboard metadata confirmed its stable URL `/d/project3-monitoring-demo/f67e2fb`.
- After reload, API returned old folder `project3-monitoring-demo` and new folder `project3-monitoring-folder`. The one provisioned dashboard is under the new folder. Its database ID and UID are unchanged, version moved from 1 to 2, all seven panels remain, and the stable URL is unchanged. Sanitized before/after payloads are in `before-*.json` and `after-*.json`.
- Isolated headless Chromium `149.0.7827.22` loaded `/dashboards`, found both folders, and expanded `Project 3 Monitoring`; the dashboard appeared as its child and no RangeError appeared. It opened the new folder route and the stable dashboard route. All seven panel headings were present in the rendered dashboard DOM, with zero browser console errors. Screenshots are `browser-dashboards-folder-expanded.png`, `browser-folder-expanded.png`, and `browser-dashboard-rendered.png`; structured output is `browser-regression.json`.
- Prometheus active targets `api1`, `api2`, and `backend` all remained `up`, with empty scrape errors (`after-targets.json`).
- At final inspection all seven project containers were healthy with restart count zero; Grafana and Prometheus named volumes remain present (`containers-final.txt`, `volumes-retained.txt`). No `/work` request was made. No app, Redis, or monitoring container was restarted or stopped.

## Validation and limitations

- Static YAML/JSON UID assertions passed: provider folder UID differs from dashboard UID; stable dashboard UID is preserved. `git diff --check` passed.
- Provisioning reload returned HTTP 200. Authenticated API checks, actual list expansion, folder route, dashboard route, panel headings, target status, and final container health passed.
- The rendered 1280×900 screenshot shows the upper six panels; all seven headings are present in the dashboard DOM. The initial smaller viewport showed only two headings before the page was resized; that was viewport/lazy rendering, not a query or provisioning failure.
- Local unauthenticated socket access was sandbox-denied on the first read attempt; the authorized read-only check succeeded under escalation. Credentials were read from the existing ignored file inside the local scripts and were not emitted or saved.
- The legacy empty folder is intentionally retained. The Grafana DB and both named volumes remain in place.
