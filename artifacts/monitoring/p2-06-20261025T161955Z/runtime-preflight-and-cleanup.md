# Preflight và khôi phục runtime P2-06

## Giới hạn Docker socket và fingerprints

Kiểm tra read-only trên runtime trước khi cleanup:

- Docker socket bên trong Alloy: mode `660`, owner `0:1001`; Alloy chạy UID/GID `473:473` và supplemental group `1001`, nên group có quyền socket. Alloy v1.21.2 dùng Docker Engine `29.3.1`; Docker client/server API đều `1.54`, server minimum API `1.40`. (Không nhầm số phiên bản Engine với API.)
- Chỉ Alloy mount `/var/run/docker.sock`, bind mount `ro`; Prometheus/Grafana không mount socket. Cả 9 monitoring container đều `Privileged=false`. Grafana/Prometheus cấu hình không đưa socket ra ngoài; không cấu hình daemon TCP.
- Tất cả runner cases ghi actual image IDs trong `artifacts/console/<RunID>/result/custom-repeat-1/images.json` và `image-inspect.json`. Pinned monitoring references theo Compose: `redis:7.4.2-alpine`, `nginx:1.28.0-alpine`, `prom/prometheus:v3.15.0`, `grafana/grafana:12.4.11`, `grafana/loki:3.7.0`, `grafana/alloy:v1.21.2`.
- Mapping image tag → container image ID/repo digest lúc cleanup được chụp read-only trong [`runtime-images.json`](runtime-images.json); mapping container IDs, gồm API/backend custom image identities, ở bảng dưới đây. Không in `Env` hoặc secret.
- Fingerprints cấu hình không chứa secret:

| Tệp | SHA-256 |
|---|---|
| `compose.observability.yaml` | `0e350aa28774d7aaf2a3b00f81584c9a0dd40cccdbe5f60851d6e3204ee8f10e` |
| `deploy/monitoring/alloy/config.alloy` | `88f7af55f22c97a740185888ac7eec46d1247970955b459901e9f1267ec492b3` |
| `deploy/monitoring/prometheus.yml` | `53af6b7daf69795189356e35ed37461019924be5899ad92a07c39d500c5730e2` |
| `deploy/monitoring/loki.yml` | `1cbb07cccfce7354f592b296a3a2eb596e56d53608d1b8fcf9be325a2c82a4ef` |
| `deploy/monitoring/grafana/provisioning/datasources/loki.yml` | `83d5c921075963d21f3af3779b5be8897e8914a27b104c8aff09a6a740d6f1d8` |
| `deploy/monitoring/grafana/provisioning/datasources/prometheus.yml` | `6f0facd04df4e5f7130269ff49b5858e8638045c855da15baeaa59fd69ea1ccb` |
| `deploy/monitoring/grafana/provisioning/dashboards/provider.yml` | `5cfd59e0bd9b6690e50d5fe21d5000658ae7d460a29a75862c171303800254e2` |
| `deploy/monitoring/grafana/dashboards/project3-overview.json` | `7e5bf354cea6384dd5d9fd2378479b3c88e386c26395598b0a51f77f6808f516` |

## Trạng thái được khôi phục

Sau case cuối, xác nhận manifest research không tồn tại và `flock -n artifacts/.research-pilot.lock` thành công. Runner đã cleanup riêng research stack. Console/browser do phiên tạo đã đóng; port 8090 không còn listener. Không còn research-pilot/loadgen process (kết quả kiểm tra tiến trình chỉ phản chiếu shell tự kiểm tra).

Đã stop đúng chín container được xác nhận ban đầu ở trạng thái stopped, không xóa/recreate; ID đầy đủ giữ nguyên:

| Container | ID | Image reference hiện hành |
|---|---|---|
| Loki | `9c0454b02c421ae439c71faeca7a9804d38904bbfc4fca974b022a3247c1e48c` | `grafana/loki:3.7.0` |
| Alloy | `3ecce63f53725bf7576ac7e9ffd6982e00b4bbb96005cee2818c95bf0dca6497` | `grafana/alloy:v1.21.2` |
| Nginx | `a589a0189908b0fc4d06d6610015119fe88009615b299afb01ee189453d58bff` | `nginx:1.28.0-alpine` |
| API2 | `272da800ef2e0cbc85756f387c8a0668f7676e89cb3fd26820ab2db069e9f1bb` | `project3-monitoring-demo-api2` |
| API1 | `663fb5cc9be00572ca4bcc3c93569a4073fd3574c33ee5e51bdf03b65a2b7c78` | `project3-monitoring-demo-api1` |
| Backend | `7c5e8deb126d996ada850a4a62c85b880dcab39d2baeaefa4b7ae9999bd86b8d` | `project3-monitoring-demo-backend` |
| Grafana | `86acfe9546c27e0dcda1ac54404d1b27991c89981e998ed6fd64683d47634ab1` | `grafana/grafana:12.4.11` |
| Prometheus | `1e2bcb4bcd72af0b334634a32f662a4cc528ec51dc4e72fd98bbd3a57c051b30` | `prom/prometheus:v3.15.0` |
| Redis | `8be2ce053153fee41208fcd16d570f4a3888765ddaacca0a75fa2b56534890a4` | `redis:7.4.2-alpine` |

Giữ nguyên bốn volume (`alloy-data`, `grafana-data`, `loki-data`, `prometheus-data`) và hai bridge network: `project3-monitoring-demo_default` ID `d20674608854109b09bd9829748e95c4c3d92fde7841f3409ea3bedde7df8cd8`; `project3-monitoring-scrape` ID `78c1621e80052f3e8e85584f5109e88c807a428d84e8ca60009e36f55c3175ae`. Trạng thái sau stop: cả chín container `Exited (0)`, bốn volume và hai network còn tồn tại.

## Phạm vi xác minh được tái sử dụng

Kiểm thử static/socket/dashboards và các xác minh lifecycle đã có từ P2-04/P2-05 được tham chiếu, không lặp lại. Case 4 toast Explore `Unknown error` đã được giữ nguyên và đối chiếu response status/số frame; nguyên nhân toast chưa xác định dù required query thành công. Case 5/6 giữ cả kết quả query đầu (không có startup logs trong load window) và query chẩn đoán mở rộng tường minh, không ghi đè kết quả đầu.

## Phiên read-only retained-data bổ sung cho row3 panel7

Sau khi phát hiện ảnh row3 panel7 cũ thực ra thuộc row2, root cho phép mở lại retained data mà không có load. Preflight xác nhận hai container gốc đang stopped với cùng ID, volume và network còn nguyên. Chỉ start Prometheus `1e2bcb4bcd72af0b334634a32f662a4cc528ec51dc4e72fd98bbd3a57c051b30` (started `2026-10-25T17:04:34.230199410Z`) và Grafana `86acfe9546c27e0dcda1ac54404d1b27991c89981e998ed6fd64683d47634ab1` (started `17:04:34.507664204Z`); cả hai health/readiness OK. Bảy monitoring container khác giữ stopped state.

Browser mở chính xác row3 runner URL (job `project3-console-run`, rate `4s`, `from=1792945951420`, `to=1792945981419`), bấm End và thấy panel `API backend errors (/s)`/api1/api2. Panel query HTTP200, không error, hai series × ba evaluation points; screenshot và sanitized result tại `row3-panel7-correction.md`, `row3-panel7-verification.json`, `supplemental/row3-grafana-panel7-corrected.png`, raw response `browser-raw/row3-panel7-response.json`. Không đăng ký target, không tạo run, không thay config.

Đóng hai browser tabs trước khi dừng đúng hai ID ở trên: Grafana `FinishedAt=2026-10-25T17:06:24.637480163Z`, Prometheus `17:06:24.726318387Z`. Sau stop xác nhận cả chín container `Exited (0)`, IDs nguyên vẹn; bốn volume và hai network IDs không đổi.
