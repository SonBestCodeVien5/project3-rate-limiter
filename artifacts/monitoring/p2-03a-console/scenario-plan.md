# Kế hoạch một attempt P2-03A

Người dùng cấp G1/G2/G3 cho P2-03A; dừng sau gói này. G3 chỉ được bắt đầu bằng nút **Chạy benchmark** hiện có trong Console, qua `research-pilot.sh` và loadgen hiện có.

- Workload custom normal, toàn bộ traffic legitimate; không có abusive traffic.
- Redis shared state, Fixed Window, fail-closed; 2 API.
- Quota 20 request / 1 giây.
- Backend capacity 4, service time 50 ms.
- Offered load 20 RPS, duration 30 giây, 1 repetition.
- Monitoring opt-in; job `project3-console-run`; source fixed `project3-demo` kiểm tra riêng.
- Chính xác 1 attempt tổng cộng, không retry và không case bổ sung. Lỗi setup/load, generator drops và failures đều phải ghi nhận.
- Không có `/work` probe hoặc workload setup ngoài attempt G3 này. Health/JSON metrics/exposition/scrape/config/browser được phép trong G2.
- Quan sát pre-load/lookback và drain/final scrape ghi UTC riêng; không tăng hoặc dịch workload 30 giây.
- Không P2-04+, Loki/Alloy, Redis outage, T09/T10 hoặc push.

Coverage P2-06 chỉ tính khi source/config/workload/topology/instrumentation khớp suite khai báo. Các case khác vẫn pending và không được chạy trong phiên này. Runtime/effective config, images và timing phải được ghi sau khi xác minh.

Giữ hai named volumes monitoring, credentials, artifacts và evidence lịch sử. Research resources chỉ cleanup qua owner hiện hữu; để monitoring stack sẵn dùng. Không `down -v`, prune hoặc FLUSHDB.
