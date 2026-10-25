# Trạng thái tài nguyên ban đầu

- project3-monitoring-demo: đúng 7 container có sẵn, tất cả Exited (0) khoảng 12 giờ; không có project3-research-lab container hoặc active.json.
- Volumes có sẵn: project3-monitoring-demo_prometheus-data, project3-monitoring-demo_grafana-data.
- Networks có sẵn: project3-monitoring-demo_default, project3-monitoring-scrape.
- Không có container Alloy hoặc Loki. Chỉ thiếu hai image đã pin grafana/loki:3.7.0 và grafana/alloy:v1.21.2; cả hai được pull theo quyền G2.
- Docker daemon 29.3.1, API 1.54, minimum 1.40.
- Socket trong worker namespace: Unix socket 0660, 65534:65534. Trong mount của Alloy: Unix socket 0660, 0:1001; Alloy chạy 473:473 với supplementary GID 1001.
