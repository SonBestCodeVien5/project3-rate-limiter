# Project 3: Giới hạn lưu lượng phân tán

Project nghiên cứu Fixed Window và Token Bucket trên nhiều API instance, so sánh local state với Redis shared state, và đo khả năng bảo vệ backend khi có traffic bất thường cùng client hợp lệ. Flash sale là bối cảnh giả định; đây không phải API Gateway production.

Bắt đầu ở [hướng dẫn đọc tài liệu](docs/README.md). Tài liệu nguồn trên Drive là căn cứ yêu cầu; [thiết kế triển khai](docs/IMPLEMENTATION.md) ghi lựa chọn kỹ thuật. [Roadmap](docs/PROJECT_ROADMAP.md) là lộ trình học đề xuất. Trạng thái task ở [kế hoạch còn lại](docs/REMAINING_WORK_PLAN.md); cổng đo ở [readiness](docs/experiments/PROTOCOL_READINESS.md).

**Trạng thái 24/10/2026:** T09/T10 hoàn tất; T11 đã tích hợp bản nháp, còn định dạng/rubric chờ. T12 gói demo/source đã kiểm tra; T13 chưa có deck PowerPoint. P2-03 fixed metrics/Grafana đã kiểm tra. P2-03A đã có monitoring opt-in trên **Chạy benchmark**, nhưng attempt G3 duy nhất thất bại trước loadgen; Console→Grafana acceptance và P2-06 coverage còn pending, không retry trong phiên. Xem [sổ P2](docs/monitoring/PHASE2_PLAN.md) để biết trạng thái/gate. Nếu cần chạy app cùng monitoring, theo [runbook monitoring](docs/monitoring/RUNBOOK.md).

## Chạy prototype (base Compose, không gồm monitoring)

Các lệnh dưới đây chỉ chạy prototype bằng base Compose; chúng không khởi động Prometheus/Grafana. Muốn chạy app cùng monitoring, dùng riêng [runbook monitoring](docs/monitoring/RUNBOOK.md). Cần Go 1.26.1 trở lên, Docker Compose, Bash, curl và GNU `timeout`.

```bash
docker compose up -d --build --wait
curl -i -X POST -H 'X-Client-ID: buyer-1' http://localhost:8080/work
curl http://localhost:18083/metrics
docker compose down
```

Mặc định dùng Redis Fixed Window, 2 API instance, Q=20/1s và backend capacity=10/service time=50ms. Biến môi trường của stack nằm trong [Compose](compose.yaml); cấu hình runner/UI ở [hướng dẫn Console](docs/CONSOLE.md); lệnh runner/pilot nằm trong [scripts README](scripts/README.md). Ví dụ này không cấp quyền chạy thí nghiệm hay runtime monitoring.

`X-Client-ID` là định danh workload, không phải authentication. API trả 429 khi quota hết, 503 khi fail-closed hoặc backend overload, 502 khi lỗi transport backend. T09/T10 đã hoàn tất; không chạy thêm tải hoặc ghép telemetry P2 vào kết quả nghiên cứu. Xem [kết quả T10](docs/analysis/T10_RESULTS.md) và [gói demo T12](docs/DEMO_SCRIPT.md).
