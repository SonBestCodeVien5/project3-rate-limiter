# Hiệu chỉnh bằng chứng panel 7 — case 2 và 3

## Phát hiện

Hai tệp `supplemental/row2-grafana-panel7.png` và `supplemental/row3-grafana-panel7.png` có cùng SHA-256 `49d5e3a1fc239881e59dd67fcae2b0cc918a6482eb55d327e64a04bd6c7ebf21`, nghĩa là cùng nội dung byte. Không được dùng ảnh thứ hai để chứng minh panel 7 của case 3.

Raw Playwright screenshot `browser-raw/playwright-output/page-2026-10-25T16-36-50-914Z.png` và `...16-37-29-993Z.png` cũng có hash đó. Cả hai hiển thị Grafana range Bangkok `23:28:51`–`23:29:21` UTC+7 (`16:28:51`–`16:29:21Z`), tức chính xác case 2 normal/local. Chúng chứng minh panel 7 case 2.

Row3 normal/Redis có raw screenshot riêng `browser-raw/playwright-output/page-2026-10-25T16-34-36-181Z.png`. Ảnh hiển thị job `project3-console-run`, rate `4s`, retained range Bangkok `23:32:31`–`23:33:01` (`16:32:31`–`16:33:01Z`), khớp row3; nhưng chỉ sáu panel đầu xuất hiện. Bản copy nguyên trạng để đọc là [row3 dashboard overview — sáu panel](supplemental/row3-grafana-six-panels.png), SHA-256 `3d5f5f69a7377f5425f15b2f522fe7a3859e3245a574de2de21c0bc28d070ee4`.

Trong lần audit ban đầu, các Playwright snapshots còn lại khoảng 16:34–16:37 chỉ ghi `Loading Grafana`; snapshot Console 16:33:20 có đúng row3 run ID và Grafana URL nhưng không chứa DOM Grafana. Khi đó chưa có row3-specific DOM/network/screenshot nào chứng minh panel 7 sau scroll, nên trạng thái được ghi incomplete trước khi có phê duyệt xác minh mới.

## Hiệu chỉnh verdict ban đầu

- Case 2 panel 7: verified với ảnh đúng range.
- Case 3: overview 6 panel đúng range verified; panel 7 ban đầu **incomplete/unverified**. Ảnh có tên `row3-grafana-panel7.png` và manifest checksum cũ được giữ nguyên để bảo toàn audit trail, nhưng được đánh dấu misattributed.
- Các row khác không bị ảnh hưởng. Khẳng định ban đầu `7/7 panel` cho case 3 trong `row3-checks.md` và `supplemental-dashboard-panels.md` được thay bằng finding này.
- Runtime loads, runner summaries, Loki case evidence và teardown không thay đổi. Đây là correction-only, không tạo run mới.

## Tái xác minh chỉ đọc từ retained data

Theo phê duyệt của root, mở lại đúng Grafana URL row3 (job `project3-console-run`, rate `4s`, `from=1792945951420`, `to=1792945981419`), rồi bấm End. Phiên bắt đầu khi hai container gốc đang stopped: Prometheus `1e2bcb4b...` và Grafana `86acfe95...`; chỉ start đúng hai ID đó, không recreate. Prometheus readiness và Grafana health đều OK; bảy container khác vẫn stopped.

Dashboard DOM có `API backend errors (/s)` và series api1/api2. Query PromQL panel 7 dùng đúng job/time range, HTTP 200, không error; response có 2 frame, mỗi series 3 evaluation points tại `1792945950000`, `1792945965000`, `1792945980000`, values đều 0. Screenshot mới: [row3 panel 7 verified](supplemental/row3-grafana-panel7-corrected.png). Sanitized query/runtime record: [row3-panel7-verification.json](row3-panel7-verification.json); response thô: `browser-raw/row3-panel7-response.json`.

Phiên chỉ đọc chạy từ container start `2026-10-25T17:04:34.230199410Z` / `17:04:34.507664204Z` tới stop `17:06:24.726318387Z` / `17:06:24.637480163Z`; browser tabs đóng trước khi stop. Sau đó xác nhận cả 9 container `Exited (0)`, IDs nguyên vẹn, bốn volume và hai network còn nguyên. Không có load, target registration hay đổi config. **Verdict cuối: case 3 panel 7 verified bằng bằng chứng mới; ảnh gán nhầm ban đầu vẫn bị loại trừ.**
