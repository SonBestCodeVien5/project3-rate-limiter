# Bổ sung xác minh dashboard sau khi cuộn — case 1–3

Ban đầu ảnh toàn trang được chụp trước khi Grafana lazy-render các panel ngoài vùng cuộn hiện tại, nên chỉ thấy sáu panel đầu. Không có lỗi provisioning: mở lại từng **retained range** sau cleanup, bấm End để Grafana render phần cuối, rồi xác nhận DOM có panel `API backend errors (/s)` với series api1/api2 và không có Grafana alert/query error. Đây là kiểm tra UI bổ sung sau run, không gửi thêm request và không thay đổi telemetry.

| Case | Job / rate / load range được mở lại | Kết quả scroll tới panel cuối | Ảnh bổ sung |
|---|---|---|---|
| 1 normal/none `20261025T162327-4e8d83985f96` | `project3-console-run`, `4s`, `16:23:53.539Z`–`16:24:23.539Z` | 7/7 panel, panel API backend errors có api1/api2; không alert | [case 1](supplemental/row1-grafana-panel7.png) |
| 2 normal/local `20261025T162826-777671c4739c` | `project3-console-run`, `4s`, `16:28:51.425Z`–`16:29:21.425Z` | 7/7 panel, panel API backend errors có api1/api2; không alert | [case 2](supplemental/row2-grafana-panel7.png) |
| 3 normal/Redis `20261025T163206-aabcac391d9b` | `project3-console-run`, `4s`, `16:32:31.420Z`–`16:33:01.419Z` | Ảnh này trùng byte với case 2 và không chứng minh row3 panel cuối; correction-only retained-data check sau đó xác nhận 7/7 | [case 3 verified](supplemental/row3-grafana-panel7-corrected.png); [provenance note](panel7-correction.md) |

Case 3 Loki Explore chạy sau cleanup trong range startup `16:32:15Z`–`16:33:10Z`, query project/service allowlist + `server started`; trả 3 startup JSON lines, labels project/service/service_name. Ảnh: [case 3 Loki](supplemental/row3-loki-startup.png). Case 1–2 Loki results đã ghi ở checks tương ứng; đây không thay các screenshot ban đầu mà bổ sung phần chưa hiện do scroll. Lịch sử nhầm attribution và việc xác minh row3 bằng hai container retained-data được ghi tại `panel7-correction.md`.

## Độ chính xác thời gian và panel

`console-monitoring.py` đổi epoch millisecond bằng `round(timestamp*1000)`. Delta `Grafana from - load_started_at`: case 1 `−0.147045 ms`; case 2 `−0.343854 ms`; case 3 `+0.443138 ms`. End-bound theo cấu hình duration có độ phân giải millisecond. Bounds không bị người vận hành dịch; sai số chỉ do chuyển sang millisecond. Các đường dashboard thể hiện query evaluation points theo độ phân giải Grafana, không khẳng định raw scrape sample count và không thay summary/trace của runner.

## Bổ sung case 4–6

Giữ nguyên screenshot ban đầu và checksum manifest từng row. Các ảnh dưới đây là supplemental mới sau khi mở chính xác Grafana URL do runner tạo và cuộn End để lazy-render panel thứ bảy.

| Case | Run ID | Job / rate / range | Panel 7 | Ảnh |
|---|---|---|---|---|
| 4 mixed/none | `20261025T163843-e758f28f6b94` | `project3-console-run`, `4s`, `16:39:08.057Z`–`16:39:38.056Z` | `API backend errors (/s)` có api1/api2; không alert | [Grafana](supplemental/row4-grafana-seven-panels.png) |
| 5 mixed/local | `20261025T164349-295d3f8931d4` | `project3-console-run`, `4s`, `16:44:15.569Z`–`16:44:45.568Z` | `API backend errors (/s)` có api1/api2; không alert | [Grafana](supplemental/row5-grafana-seven-panels.png) |
| 6 mixed/Redis | `20261025T164831-642d9b71ee0d` | `project3-console-run`, `4s`, `16:48:55.074Z`–`16:49:25.074Z` | `API backend errors (/s)` có api1/api2; không alert | [Grafana](supplemental/row6-grafana-seven-panels.png) |

Case 5/6: Loki query chính ban đầu ở load window trả HTTP200 nhưng 0 startup rows; giữ nguyên response đó. Query startup diagnostic chỉ đọc, mở rộng khoảng thời gian để bao trùm stack initialization trước load, tìm thấy API và backend JSON lines còn sau cleanup. Đó là bằng chứng retention của startup logs, không đổi dashboard bounds hay load duration. Details/response bodies nằm trong `row5-checks.md`, `row6-checks.md` và `browser-raw/`.
