# Sanitized command and request ledger

All times UTC; all API requests were local to `127.0.0.1`. No `/work` requests were sent.

1. `2026-10-23T14:46:45Z` — GET `/api/search?type=dash-folder`, GET `/api/search?type=dash-db`, GET `/api/dashboards/uid/project3-monitoring-demo`, GET `/api/health`. The local Python process read `.secrets/grafana_admin_password` internally for Basic authentication and saved only allowlisted metadata fields in `before-*.json`.
2. `2026-10-23T14:47:24Z` — POST `/api/admin/provisioning/dashboards/reload`; HTTP 200, `{"message":"Dashboards config reloaded"}` (`reload-result.json`).
3. `2026-10-23T14:47:34Z` — Read-only repeats of folder/dashboard search, dashboard UID API, Grafana health, and Prometheus `/api/v1/targets?state=active`; sanitized responses saved as `after-*.json`.
4. `2026-10-23T14:49:13Z` and `2026-10-23T14:49:51Z` — Local isolated headless Chromium sessions loaded Grafana UI. The later bounded session explicitly clicked the rendered `Expand folder Project 3 Monitoring` control on `/dashboards`, opened the folder, then opened the stable dashboard URL. No credentials were passed in a tool argument; the local script read the ignored secret file and returned only UI state/screenshots.
5. `2026-10-23T14:50:33Z` — Final browser state and screenshots captured using Chromium 149.0.7827.22 at a 1280×900 viewport; all seven dashboard panel headings present; no browser console errors.
6. `2026-10-23T14:52:13Z` — Read-only Docker inspect for containers labeled `com.docker.compose.project=project3-monitoring-demo` and volume listing. All seven services healthy, restart count zero; two named volumes retained.
7. Focused static checks: parse provider YAML and dashboard JSON, assert `folderUid != dashboard.uid`, assert stable dashboard UID and intended folder UID/title; run `git diff --check`.

The actual running Grafana tag/API version was `12.4.11`; see `containers-final.txt` and `after-health.json`. No `docker compose down`, restart, volume operation, app/Redis action, demo load, or Console action occurred.
