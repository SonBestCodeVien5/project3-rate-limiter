# Trạng thái tài nguyên khi kết thúc

- Đã dừng cả chín container của project `project3-monitoring-demo`: bảy container có sẵn trước phiên (`api1`, `api2`, `backend`, `grafana`, `nginx`, `prometheus`, `redis`) và hai container Alloy/Loki được tạo trong phiên. Bảy container ban đầu giữ nguyên identity; không xóa container.
- Giữ nguyên bốn named volumes: `project3-monitoring-demo_alloy-data`, `project3-monitoring-demo_grafana-data`, `project3-monitoring-demo_loki-data`, `project3-monitoring-demo_prometheus-data`.
- Giữ nguyên network `project3-monitoring-demo_default` và external network `project3-monitoring-scrape`.
- Không còn container research hoặc sentinel negative-control. `artifacts/monitoring/console-targets/active.json` không tồn tại.
- Browser evidence đã chọn được sao chép vào `screenshots/`. Sau khi đóng trang Grafana, các output thô do browser tool tạo được chuyển nguyên trạng vào `browser-raw/` trong thư mục ignored này; không đưa vào commit hoặc `SELECTED_SHA256SUMS`.
