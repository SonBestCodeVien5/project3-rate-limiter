# P2-05 G2 — kiểm tra runtime logs/lifecycle

Thực hiện 25/10/2026 UTC theo quyền G2. Không gửi request /work, không chạy loadgen, benchmark, outage hoặc phân tích T09/T10. Batch giữ nguyên dữ liệu, query và registry riêng.

## Thay đổi cấu hình đã kiểm chứng

- Bỏ Loki container healthcheck gọi wget vì image pinned grafana/loki:3.7.0 không có wget, curl hay shell; Alloy phụ thuộc Loki ở trạng thái service_started. Runbook yêu cầu kiểm tra HTTP /ready từ client cùng network.
- Alloy socket supplementary GID đổi sang 1001: trong container mount socket là 0:1001 mode 0660; process chạy 473:473. GID 65534 trong worker namespace không khớp group của mount.
- Bật ingester.wal.flush_on_shutdown: true cho graceful Loki restart/recreate. Pinned binary báo WAL enabled, path hiệu lực /loki/wal, flush ban đầu false; WAL path nằm dưới named volume /loki.
- Không sửa app, endpoint JSON /metrics, renderer hoặc Console runner.

## Validators và health

- Compose config resolve: đạt.
- Prometheus promtool check config: đạt cú pháp; cảnh báo file_sd glob không khớp vì active.json đã được gỡ tại thời điểm kiểm tra.
- Loki pinned binary -verify-config: đạt với cấu hình cuối.
- Alloy validate: đạt với config cuối.
- Prometheus /-/ready, Loki /ready, Alloy /-/ready và Grafana /api/health: đạt.
- Fixed Prometheus targets: 3/3 UP (api1, api2, backend), job project3-demo. Research 4-instance no-load registration: api1…api4/backend, 5/5 UP, topology=4, project=project3-research-lab.
- API JSON /metrics và backend JSON /metrics parse được; schema JSON hiện có giữ nguyên. API requests counter vẫn 0. Không gọi /work.
- Grafana dashboard và Explore query: chi tiết/range chính xác ở browser-checks.txt; ảnh đã lưu trong screenshots/.

## Alloy → Loki → Grafana

- Fixed startup logs: query LogQL project3-monitoring-demo trong UTC 2026-10-25 04:00–04:30 trả 9 dòng: 3/service cho api1, api2, backend.
- Research no-load opt-in 2-instance: target registration/wait/remove qua console-monitoring.py; startup JSON của api1, api2, backend xuất hiện.
- Research no-load opt-in 4-instance: 5 target và 5 startup JSON logs api1…api4/backend. Lần đo first-visible cuối cùng ghi Compose bắt đầu 04:22:25.639Z, healthy 04:22:36.208Z, manifest registered 04:22:36.297Z; first baseline scrape 04:22:37.395Z (+1.098s), post-lookback scrape 04:22:41.398Z; query đầu tiên thấy đủ 5 service ở 04:22:43.337Z (+6.940s từ register, ≤13.340s từ source log sớm nhất). Khoảng query được lưu tại research-4-first-visible/timing.txt.
- Opt-out topology được chạy riêng, không bật target registration. Trong UTC interval chính xác ở research-opt-out-no-load/opt-out-window.txt: 0 Loki entry và 0 Prometheus research target. Renderer opt-out không có label project3.monitoring.logs hoặc network monitoring-scrape.
- Negative control project thứ ba: container backend tạm có Compose project/service labels project3-p2-05-excluded/backend, opt-in log label true và scrape-network attachment. Healthz trả 200, startup JSON parse được; sau 20 giây query exact range có 0 Loki entries. Xem excluded-project-window.txt và excluded-project-startup-sanitized.json.
- Loki indexed labels: project, service, service_name. service_name là label ổn định trùng tên service; detected_level chỉ có trong query result và không nằm trong endpoint indexed label names. Project values chỉ fixed/research; service values chỉ api1…api4/backend. Không thấy Redis, Nginx, Prometheus, Grafana, Alloy hoặc ID/run/case labels.
- Loki query range 2026-10-25 04:00:00–04:30:00 UTC có 22 startup entries hợp lệ JSON: 9 fixed, 13 research opt-in; 0 JSON parse failures. Chênh source JSON time so với Loki/Docker envelope timestamp lớn nhất 1.847 ms; cả hai UTC. Grafana browser hiển thị cùng events ở Asia/Bangkok, UTC+07:00.
- Docker discovery thực tế chuyển fixed/research opt-in logs, nhưng không chuyển sentinel của project thứ ba dù sentinel có nhãn opt-in và cùng scrape network. Redis/Nginx và các monitoring service cũng không xuất hiện trong runtime label values.

## Restart/replay và phục hồi

- Alloy state volume project3-monitoring-demo_alloy-data giữ file loki.source.docker.project3/positions.yml tại /var/lib/alloy/data, mode 0600. Alloy restart trở lại ready trong 2s; 9 fixed entries trước/sau giữ nguyên, không quan sát duplicate trong tập recent. Đây không phải exactly-once guarantee.
- Một Loki graceful restart ban đầu có sai khác trong rolling 20m query: 2 startup entries/service trước, 1/service sau; các dòng 04:09 UTC xuất hiện lại sau lần Alloy restart tiếp theo. Exact query bounds của chẩn đoán đầu không được lưu, nên không dùng làm định lượng chính thức và không kết luận nguyên nhân. Giữ lại như finding, không xóa/rewrite.
- Khi Alloy được tạo lại, hai log startup fixed cũ từ 2026-10-24 15:03 UTC bị Loki từ chối HTTP 400 entry too far behind; oldest accepted là 2026-10-25 03:14:33 UTC. Đây là dữ liệu cũ hơn cửa sổ Loki chấp nhận. Có warning context canceled khi tailer dừng trong restart/cleanup. Không đổi retention hoặc timestamp.
- Sau khi bật flush_on_shutdown, recreate Loki giữ cùng named volume; /ready trong 19s. Trên query range cố định 04:00–04:25 UTC có 12 entries trước và sau, cùng 6 project/service streams và cùng count. Retest hữu hạn này xác nhận dữ liệu của tập query được giữ qua graceful recreate; chưa thử crash/SIGKILL.
- Không tuyên bố exactly-once. Dữ liệu startup quá cũ vẫn có thể bị Loki reject khi Alloy replay lại Docker history.

## Tài nguyên và evidence

- Ghi trạng thái ban đầu tại initial-state.md, image pin/tag/ID/digest trong images.json và source/dirty state trong source.txt.
- Artifact log được lọc còn project/service, source timestamp, Loki timestamp, delta và message; không lưu Docker inspect env, password, TSDB, Loki chunks hoặc raw credentials.
- Research active manifest được gỡ theo owner record; project containers/network do phiên tạo đã được scoped cleanup. Final fixed project được stop, giữ container identity và mọi named volume.
- P2-05 pipeline/no-load G2 đạt cho fixed và research opt-in. Runner workload lifecycle, log sau workload/final scrape, cancel/SIGTERM, stale-registration incident vẫn pending; cần G3 riêng. Xem pending.md.
