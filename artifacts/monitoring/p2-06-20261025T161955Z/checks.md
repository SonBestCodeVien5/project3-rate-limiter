# Kết quả xác minh P2-06

## Kết luận

**P2-06 hoàn tất kỹ thuật theo suite sáu case đã duyệt.** Sáu lần submit Console đã hoàn tất một lần mỗi case; monitoring enrollment, scrape baseline/lookback/final, dashboard và log startup retained đều có bằng chứng. Không có lần chạy bị retry/thay thế, không dùng số liệu dashboard để suy goodput/latency/correctness. Confirmation học tập của user là gate riêng, chưa được xác nhận trong lần thực hiện kỹ thuật này.

## Kết quả từng case

| # | Case / Run ID | Summary từ runner | Monitoring và giới hạn |
|---|---|---|---|
| 1 | normal / none — `20261025T162327-4e8d83985f96` | 600/600 sent; 600 2xx; không drop/lỗi | Grafana 7 panel; Loki startup JSON có 3 dòng; scrape sau drain; ảnh/sums row1 |
| 2 | normal / local — `20261025T162826-777671c4739c` | 600/600 sent; 600 2xx; không drop/lỗi | Grafana 7 panel; Loki startup JSON có 3 dòng; scrape sau drain; ảnh/sums row2 |
| 3 | normal / Redis — `20261025T163206-aabcac391d9b` | 600/600 sent; 600 2xx; không drop/lỗi | Grafana panel7 được xác minh từ retained range bằng query HTTP200/3 points mỗi API series; ảnh lần đầu gán nhầm được giữ và loại bằng correction note |
| 4 | mixed / none — `20261025T163843-e758f28f6b94` | 3600/3600 sent; 2028 2xx, 1572 5xx; 0 drop/429/timeout/transport | Grafana 7 panel; required Loki query HTTP200/3 rows; generic Explore toast `Unknown error` không rõ nguyên nhân |
| 5 | mixed / local — `20261025T164349-295d3f8931d4` | 3600 scheduled; 3599 sent, 1 `schedule_backlog` drop; 1223 2xx, 1759 429, 617 5xx; 0 timeout/transport; 600 legitimate sent/472 successful | Grafana 7 panel; initial load-covering Loki query 0; setup window run-start→registration khớp 2 API + 1 backend startup JSON; loại row backend cũ `16:38:51.076884396Z` |
| 6 | mixed / Redis — `20261025T164831-642d9b71ee0d` | 3600/3600 sent; 905 2xx, 2393 429, 302 5xx; 0 drop/timeout/transport; 600 legitimate sent/534 successful | Grafana 7 panel; initial load-covering Loki query 0; setup window run-start→registration khớp 2 API + 1 backend startup JSON |

Outcome 5xx của case 4/5/6 và một drop ở case 5 được giữ nguyên theo runner; đây không phải điều kiện loại run. Tất cả outcome chỉ được báo từ runner artifacts.

## Ma trận kiểm tra

- **Pass:** 6/6 UI submissions; đúng profile/mode và cấu hình; revision/dirty state, topology, policy, image IDs; manifest owner và lock lifecycle; targets API1/API2/backend có baseline/lookback UP; load start/end/drain và final scrape sau drain; exact runner dashboard job `project3-console-run`, rate `4s`, bảy panel sau lazy render cho đủ sáu case (row3 panel7 được bổ sung bằng read-only retained-data query/screenshot); case-owned startup JSON còn truy vấn được sau cleanup; sáu attempt không vượt 30s/case hay 120 RPS.
- **Fail:** không có runner/case failure; mixed status/drop counts là workload outcomes được giữ nguyên.
- **Incomplete/giới hạn:** Case 4 Explore generic toast chưa giải thích; query chính HTTP200 và ba dòng JSON nên query-specific check pass, nhưng nguyên nhân toast/UI-clean chưa kết luận. Case 5/6 primary load-covering Loki query 0 dòng; startup xảy ra trước load nên giữ nguyên 0 và xác thực riêng query setup range theo timestamps thuộc run-start→registration. Case 5 broad query có một backend row cũ, loại trừ rõ ràng. Dashboard evaluation points không phải raw scrape sample count.
- **Skipped:** 0 planned case; không có P2-07/P2-08, outage, restart, prune, T09/T10 hay lượt thử bổ sung.

## Revision, thời gian và artifacts

Rows 1–5 ghi revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; row6 ghi `31bc3389bc3d4a3f21978dde9fb070723ccf56b0`. Commit xen giữa chỉ đổi `docs/context/SESSION_CHECKPOINT.md` và `docs/context/SOURCE_INDEX.md` (documentation-only); không đổi code/runtime. Tất cả runner ghi dirty state `?? .playwright-mcp/`; browser raw output được giữ trong batch sau cleanup. Bounds Grafana được runner serialize ở millisecond, không dịch tay: row1 `−0.147045 ms`; row2 `−0.343854 ms`; row3 `+0.443138 ms`; row4 `+0.064217 ms`; row5 `+0.288433 ms`; row6 `−0.244320 ms` so với load start. Query `to` tương ứng trong runner URL theo độ phân giải millisecond. Dashboard hiển thị query evaluation points; runner artifacts là nguồn offered/scheduled/sent/drop/response/latency.

Scenario trước tải: [`scenario-plan.md`](scenario-plan.md); ledger sáu attempt: [`attempt-ledger.md`](attempt-ledger.md); correction row3 panel: [`panel7-correction.md`](panel7-correction.md); ghi chú panel lazy-render: [`supplemental-dashboard-panels.md`](supplemental-dashboard-panels.md); Docker/config/image identity và cleanup: [`runtime-preflight-and-cleanup.md`](runtime-preflight-and-cleanup.md), [`runtime-images.json`](runtime-images.json); chọn timestamp/labels Loki không kèm log line: [`loki-startup-ownership.json`](loki-startup-ownership.json). Raw ignored runner artifacts: `artifacts/console/<RunID>/`; raw Playwright captures: [`browser-raw/`](browser-raw/). Manifest hiệu chỉnh mới: [`FINAL_SELECTED_SHA256SUMS-v2`](FINAL_SELECTED_SHA256SUMS-v2).
