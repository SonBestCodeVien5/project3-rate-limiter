# Case 4 — mixed / none

Run ID: `20261025T163843-e758f28f6b94`. Một submit qua Console UI, run `completed`. Source revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; runner ghi dirty `?? .playwright-mcp/` (browser output trong phiên).

## Runner và vòng đời

- Cấu hình: 2 API; Fixed Window Q20/W1s; mode none; fail-closed label; backend capacity 4/service 50ms; mixed tổng 120 RPS, trong đó 20 RPS legitimate và 100 RPS abusive; 5 legitimate client keys; max-inflight 200; timeout 2s; max schedule lag 100ms; 30s; repeat 1.
- Runner summary: 3.600 scheduled/sent, 0 generator drops; 2.028 HTTP 2xx, 1.572 HTTP 5xx, 0 HTTP 429/timeout/transport error; 3.600 backend-confirmed arrivals; 600 legitimate sent, 265 legitimate 2xx. Đây là outcome workload mixed/none có backend overload; không suy thành quota correctness/pass.
- Load UTC `2026-10-25T16:39:08.056935783Z`–`16:39:38.056Z`; drain `16:39:38.100149487Z`; final scrape API1/API2/backend `16:39:38.298Z`; deregistration `16:39:38.301Z`.
- Baseline `16:39:02.966Z`; lookback `16:39:02.967Z`–`16:39:06.972Z`; post-lookback scrape `16:39:06.970Z`.
- Manifest được owner gỡ và research project được cleanup; lock nhả.

## Monitoring sau cleanup

Grafana đúng job `project3-console-run`, rate `4s`, load range `16:39:08.057Z`–`16:39:38.056Z`. Sau cuộn đến cuối, đủ bảy panel render; data thể hiện API offered, backend arrivals/success/overload và API backend errors; không dashboard alert. Ảnh: [Grafana bảy panel](supplemental/row4-grafana-seven-panels.png). Không suy request counts từ evaluation points.

Loki Explore trong UTC `16:38:45Z`–`16:39:45Z`, query project/service allowlist + `server started`, hiển thị 3 startup JSON rows còn sau cleanup. Query Inspector: một required query, 3 rows; response status 200, không có error. Logs-volume query cũng HTTP 200, 2 frames/rows và không error. Browser console 0 errors. Có một generic toast `Unknown error` thoáng hiện trong Explore; nguyên nhân toast chưa xác định, dù hai query response và labels/index-stats requests đều 200. Vì vậy ghi nhận toast là giới hạn UI; required startup query vẫn có kết quả hợp lệ. Ảnh query: [Loki](supplemental/row4-loki-query.png); response bodies được giữ ở raw browser capture và checksum sau khi chuyển vào `browser-raw/`.

## Verdict case

Runner, scrape, Grafana bảy panel, Loki required query và retention sau cleanup đều có evidence. Mixed/none trả nhiều HTTP 5xx như nêu trên; không loại lượt hoặc retry. UI toast không có lỗi trong response query chính nhưng vẫn được lưu như một quan sát chưa giải thích.

Raw runner artifacts giữ ở `artifacts/console/20261025T163843-e758f28f6b94/`.
