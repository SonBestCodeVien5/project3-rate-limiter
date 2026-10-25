# Allowlist và nguồn bị loại

- Runtime labels trong Loki: indexed labels project, service, service_name; detected_level chỉ xuất hiện trong kết quả query, không nằm trong API danh sách indexed labels.
- Project values thấy trong Loki: project3-monitoring-demo, project3-research-lab. Service values: api1…api4, backend; không có redis, nginx, prometheus, grafana, alloy, container ID/name, Run ID hoặc case ID.
- Alloy thực tế kết nối Docker API sau khi sửa supplementary GID; fixed log streams và research opt-in log streams được thấy. No-load research opt-out chạy riêng trong UTC interval ghi tại research-opt-out-no-load/opt-out-window.txt: 0 Loki entries và 0 Prometheus research targets. Renderer opt-out cũng không thêm label project3.monitoring.logs hoặc network monitoring-scrape.
- Negative control thực tế: một backend container tạm dùng image app đã build, có Compose project/service labels project3-p2-05-excluded/backend, nhãn opt-in project3.monitoring.logs=true và gắn scrape network. Healthz 200 và startup JSON parse được; sau 20 giây, query exact UTC interval có 0 Loki entry cho project3-p2-05-excluded. File query window ghi thời gian cụ thể. Container và network attachment được dọn sau kiểm tra.
- Prometheus và Grafana không mount Docker socket; Alloy là service duy nhất có bind mount socket. Không expose Docker daemon TCP hoặc bật privileged.
