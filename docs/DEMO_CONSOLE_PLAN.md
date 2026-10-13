# Kế hoạch Demo Console cho Project 3

**Ghi chú hiện trạng 13/10/2026:** nội dung dưới đây giữ bản đề xuất ngày11/10, không phải tiến độ triển khai hiện tại. Console đã có UI và kiểm chứng tích hợp; xem [CONSOLE](CONSOLE.md) và [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md). Các phần mở rộng trong đề xuất vẫn không tự trở thành yêu cầu nghiên cứu.

**Trạng thái:** đề xuất để tìm hiểu và lập kế hoạch; chưa phải quyết định triển khai hay thay đổi phạm vi đã được giảng viên duyệt.  
**Cập nhật:** 11/10/2026  
**Mục tiêu:** mô tả phương án tạo một trang web để cấu hình, kích hoạt, theo dõi và trình bày benchmark hiện có trong buổi demo.

## 1. Tóm tắt đề xuất

Tạo một **Interactive Benchmark Console** nhỏ chạy trên máy demo. Người dùng chọn kịch bản và các tham số được cho phép, bấm chạy, theo dõi trạng thái và metrics, rồi xem/tải kết quả của lượt chạy.

Phương án tối thiểu dùng Go, HTML và JavaScript thuần, tái sử dụng runner Bash, Docker Compose, endpoint `/metrics` và artifact hiện có. Không cần React, Grafana hay Loki cho bản đầu. Go điều khiển runner ở phía máy chủ; trình duyệt không chạy shell hoặc điều khiển Docker trực tiếp.

Đây là lớp giao diện để trình bày các phép đo rate limiting của Project 3. Nó không phải API Gateway, hệ thống policy management tổng quát hay nền tảng observability production.

## 2. Bối cảnh và trạng thái repo đã xác nhận

### 2.1 Prototype hiện tại

- Project hiện là prototype backend/CLI, chưa có UI.
- Thành phần chính: API Go, Redis, Nginx/load balancer, backend mô phỏng năng lực xử lý, load generator Go, runner Bash và analyzer Python.
- API có `/healthz`, `/metrics`, `GET/POST /work`; metrics hiện trả JSON snapshot.
- Compose mặc định có 2 API instances; cấu hình gồm mode, algorithm, fail policy, quota, backend capacity/service time.
- Các cổng hiện bind vào loopback: ingress `8080`, metrics API `18081/18082`, backend `18083`, Redis `16379`.
- Runner research dùng Compose project riêng `project3-research-lab`, mặc định ingress `18080`; topology có thể dựng 1/2/4 API.
- Runner có 11 case: `normal`, `burst-fw`, `burst-tb`, `concurrent-local`, `concurrent-redis`, `scale-1`, `scale-2`, `scale-4`, `mixed-none`, `mixed-local`, `mixed-redis`.
- Mỗi lượt lưu cấu hình Compose đã resolve, policy, log, metrics API/backend, thông tin tài nguyên Redis, dữ liệu load generator, `summary.json`, `requests.jsonl`, revision Git và các metadata liên quan.
- Load generator ghi request bị drop và schedule lag; summary có status/error/decision counts, percentile, goodput và latency của client hợp lệ.
- Runner giới hạn repetitions hiện tại ở 1..3, xác nhận Docker/Compose và từ chối nếu Compose project của runner đã có container.

Xem [README](../README.md), [Scripts README](../scripts/README.md), [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md), [compose.yaml](../compose.yaml), [research-pilot.sh](../scripts/research-pilot.sh) và [PROJECT_BRIEF](context/PROJECT_BRIEF.md).

### 2.2 Phạm vi nguồn dự án

Roadmap và Proposal đặt trọng tâm vào distributed rate limiting, Fixed Window/Token Bucket, local/Redis shared state, concurrency/atomicity, scaling, backend protection, và Redis outage có kiểm soát. Dashboard quản trị và policy management nhiều tầng là tùy chọn; observability-driven traffic control thuộc hướng mở rộng.

Vì vậy Console nên được xem là **cách vận hành/trình bày demo cho các thí nghiệm hiện có**, không phải câu hỏi nghiên cứu mới. Nếu tính nó như một phần mở rộng, cần giữ một ranh giới nhỏ và không cắt thời gian/dữ liệu cần để hoàn tất RQ1–RQ5.

Các notes repo không mô tả cụ thể “Option B” đã được loại bỏ trước đây. Do đó tài liệu này không giả định Option B là một kiến trúc cụ thể; Console chỉ có thể được xem là một lát demo nhỏ nếu nó phù hợp với định nghĩa Option B mà người dùng đã chọn trước đó.

Nguồn ưu tiên và các ghi chú liên quan:

- [Roadmap nguồn](context/sources/00_Project3_Roadmap.md)
- [Proposal nguồn](context/sources/01_Project3_Proposal.md)
- [Đánh giá lại scope](SCOPE_REASSESSMENT_2026-10-08.md)
- [Scope và tiến độ](SCOPE_PROGRESS_2026-10-11.md)
- [Project Brief](context/PROJECT_BRIEF.md)

## 3. Mục tiêu, người dùng và luồng demo

### Mục tiêu

1. Người demo chạy được một kịch bản chính mà không phải gõ nhiều lệnh Bash.
2. Người xem hiểu cấu hình thực tế đang chạy: thuật toán, state mode, số API instances, workload và backend capacity.
3. Khi benchmark đang chạy, người xem thấy trạng thái process và các metrics chính thay đổi.
4. Sau benchmark, người demo mở được kết quả, log và artifact tái lập.
5. Giao diện không làm thay đổi semantics, dữ liệu hay protocol của benchmark hiện tại.

### Luồng người dùng

1. Mở Console trên máy demo.
2. Chọn một preset (ví dụ mixed traffic, burst hoặc scaling).
3. Xem và chỉnh các tham số được mở cho preset đó.
4. Console kiểm tra giá trị, tóm tắt cấu hình sẽ chạy và cảnh báo nếu cấu hình vượt giới hạn demo.
5. Nhấn **Run**; Console tạo Run ID và bắt đầu runner.
6. Xem giai đoạn hiện tại, tiến trình và metrics trong lúc chạy.
7. Khi kết thúc, xem summary/biểu đồ, cấu hình thực tế, log và tải artifact.

## 4. Phạm vi phiên bản đầu

### Bao gồm

- Trang tổng quan demo với trạng thái runner/Compose project.
- Chọn preset benchmark hiện có.
- Thay đổi một tập tham số đã xác định và validate trước khi chạy.
- Một benchmark chạy tại một thời điểm.
- Trạng thái run: queued/starting/running/draining/analyzing/completed/failed/canceled/cleanup-error.
- Metrics trực tiếp bằng polling trong khi load generator chạy.
- Summary cuối lượt và liên kết tới artifacts/log.
- Nút hủy lượt chạy, có cleanup theo cơ chế đã xác nhận.
- Lưu cấu hình request và cấu hình Compose đã resolve cho từng Run ID.
- Chỉ bind vào loopback trong bản demo local.

### Không bao gồm trong bản đầu

- Điều khiển chính sách quota cho người dùng production.
- Đăng nhập, RBAC, multi-tenant hay triển khai public internet.
- Arbitrary shell command, Docker command hoặc tùy ý nhập tên service.
- Nhiều lượt benchmark chạy đồng thời.
- Redis Cluster/HA, Kubernetes production, service mesh hoặc API Gateway hoàn chỉnh.
- Alerting, long-term retention, distributed tracing hay profiling.
- Grafana/Loki trừ khi pilot xác nhận rõ nhu cầu mà UI/artifact hiện tại không đáp ứng.

## 5. Giao diện và thông tin hiển thị

### 5.1 Khu vực cấu hình

Nên chia thành các trường sau; trường nào được bật phụ thuộc preset:

| Nhóm | Trường có thể cung cấp |
|---|---|
| Kịch bản | `normal`, `burst`, `concurrent`, `scale`, `mixed`, Redis outage nếu được mở riêng |
| Limiter | `none/local/redis`; `fixed-window/token-bucket`; fail policy `open/closed` |
| Topology | 1, 2 hoặc 4 API instances; backend dùng chung |
| Tải | RPS tổng, RPS client hợp lệ, số client hợp lệ, duration, repetitions |
| Burst/concurrency | burst start/duration/RPS; concurrent-at/count |
| Policy | Fixed Window: limit/window; Token Bucket: capacity/refill rate |
| Backend | capacity và service time |
| Output | Run ID tự sinh; folder artifacts do Console quản lý |

Không phải tất cả tổ hợp đều là một thiết kế thí nghiệm hợp lệ. UI cần hiển thị preset và cấu hình thực tế rõ ràng; khi cho chỉnh rộng hơn, cần validate theo tổ hợp thuật toán/workload và lưu tham số đầy đủ vào metadata.

### 5.2 Metrics khi đang chạy

Hiển thị các metrics đã có hoặc có thể lấy bằng cách poll các endpoint/runner đang chạy:

- Offered/sent/dropped requests và schedule lag từ load generator.
- Phân bố HTTP: 2xx, 429, 5xx, timeout/transport error.
- Allow/reject/fail-open/fail-closed và lỗi limiter.
- Latency tổng và latency client hợp lệ (p50/p95/p99 khi số mẫu đủ).
- Goodput client hợp lệ.
- Backend attempts/confirmed arrivals, success, overload, errors, canceled.
- API instance đang nhận request; so sánh số liệu từng instance nếu scrape được.
- Redis CPU/memory hoặc resource sample, kèm nhãn rõ cách lấy và khoảng lấy mẫu.
- Giai đoạn process hiện tại, thời gian chạy, thời gian dự kiến còn lại nếu có cơ sở tính.

Không nên gắn nhãn “real-time” cho giá trị cuối cùng nếu nguồn chỉ là snapshot trước/sau lượt chạy. Cần phân biệt sample trực tiếp, counter tích lũy, delta của lượt chạy, và kết quả chỉ có sau khi generator drain/analyzer hoàn tất.

### 5.3 Kết quả sau run

- Tóm tắt cấu hình thực tế và Run ID.
- Tổng request, dropped, status/decision counts, throughput/goodput, percentile.
- Biểu đồ client hợp lệ và toàn tải được tách riêng.
- Backend arrivals/overload so với rate limit.
- Nếu có outage: timeline outage, fail-open/fail-closed, availability/recovery và giới hạn của phân tích.
- Trạng thái analyzer (`conclusive`, `inconclusive`, hoặc trạng thái hiện có), không tự suy diễn kết luận nghiên cứu.
- Liên kết xem/tải JSON, logs, config resolved, trace và analyzer output.

## 6. Kiến trúc đề xuất

```mermaid
flowchart LR
    B[Trình duyệt] -->|HTTP polling/control API| C[Go Console Controller]
    C -->|allowlisted args| R[research-pilot runner]
    R --> D[Docker Compose research lab]
    D --> M[/metrics API, Redis, backend]
    R --> A[Run artifacts, logs, summary, trace]
    M --> R
    A --> C
    C --> B
```

### Thành phần

1. **Console UI:** HTML template + CSS + JavaScript thuần được Go phục vụ. Không cần build chain frontend.
2. **Console Controller:** HTTP endpoints cho preset, validate config, tạo run, đọc trạng thái, lấy metrics và artifacts, hủy run.
3. **Runner adapter:** gọi `scripts/research-pilot.sh` bằng `exec.CommandContext` với argv tách phần tử; không ghép chuỗi lệnh shell. Chỉ map field đã validate thành flags/environment mà runner hỗ trợ.
4. **Run state:** trạng thái tối thiểu được giữ trong process memory và metadata/artifact trên đĩa; phải xác định cách khôi phục hoặc đánh dấu run dở nếu Console bị restart.
5. **Artifacts:** một folder riêng theo Run ID dưới `artifacts/`; không ghi đè folder có sẵn.
6. **Metrics sampler:** lấy snapshot định kỳ từ API/backend/Redis hoặc gọi cơ chế sampling hiện hữu. Tắt sampler sau run và ghi dữ liệu được lấy vào artifact.

### Hợp đồng API nội bộ đề xuất

Tên endpoint chỉ là thiết kế ban đầu, cần giữ nhỏ:

| Endpoint | Tác dụng |
|---|---|
| `GET /` | Trang Console |
| `GET /api/presets` | Danh sách preset và schema/giới hạn tham số |
| `POST /api/runs` | Validate config, tạo Run ID và khởi động một lượt |
| `GET /api/runs/{id}` | Trạng thái, cấu hình và tiến độ run |
| `GET /api/runs/{id}/metrics` | Metrics/sample trực tiếp hoặc snapshot mới nhất |
| `POST /api/runs/{id}/cancel` | Yêu cầu dừng process và cleanup |
| `GET /api/runs/{id}/artifacts` | Danh sách artifacts đã allowlist |
| `GET /api/runs/{id}/artifacts/{name}` | Tải file kết quả đã xác định |

Không expose endpoint kiểu `POST /shell`, truyền Docker Compose args tùy ý hay đọc path file tùy ý.

## 7. Hướng triển khai theo giai đoạn

### Giai đoạn 0 — Chốt yêu cầu và khảo sát (không đổi code)

**Việc tìm hiểu**

- Chốt vai trò của UI: demo control hay full experiment manager.
- Xác định một luồng demo chính, ví dụ `mixed-none` → `mixed-local` → `mixed-redis`, hoặc burst FW/TB.
- Lập bảng trường cấu hình cần chỉnh, giới hạn và tổ hợp hợp lệ.
- Đọc chi tiết script/runner cleanup, signal handling, sampler, artifact naming và analyzer output.
- Xác định yêu cầu cài đặt demo: cùng máy hay LAN; có internet không; máy có Go/Docker không.
- Kiểm tra Option B đã loại bỏ từ tài liệu/cuộc thảo luận gốc trước khi gắn Console với option đó.

**Đầu ra**

- Một use case demo được chọn.
- Bản wireframe sơ bộ.
- Danh sách metrics và nguồn dữ liệu.
- Quyết định scope: chỉ UI/summary hay có run control.

### Giai đoạn 1 — Read-only demo view

**Mục tiêu:** giảm rủi ro, xác nhận bố cục và metrics trước khi cho UI điều khiển process.

- Go phục vụ trang và poll một stack đang chạy.
- Hiện config/health, API/backend metrics, request thử, summary gần nhất.
- Không start/stop Docker từ UI.
- Xác nhận mọi số liệu được gắn đúng nguồn và đúng ý nghĩa.

**Tiêu chí hoàn thành:** người demo mở trình duyệt, phát request mẫu và giải thích được 429/503/502, decisions và backend arrivals.

### Giai đoạn 2 — Chạy một preset benchmark từ UI

**Mục tiêu:** thêm khả năng chọn và khởi chạy một số preset đã duyệt.

- Thêm controller và run state.
- Cho gọi một kịch bản đã allowlist, trước tiên có thể chỉ một preset mixed hoặc burst.
- Chạy tuần tự một lượt, tạo Run ID/folder mới.
- Poll trạng thái runner và metrics; hiển thị log/progress.
- Khi complete, đọc summary và cho tải artifacts.
- Kiểm thử các lỗi: Docker không sẵn sàng, port conflict, script fail, controller restart, client đóng trang.

**Tiêu chí hoàn thành:** bấm Run tạo đúng một run riêng, hiển thị trạng thái, cleanup đúng container của project, lưu config và artifacts; không ảnh hưởng stack ngoài phạm vi.

### Giai đoạn 3 — Tham số hóa có giới hạn

**Mục tiêu:** cho tùy chỉnh các benchmark variables hữu ích mà vẫn có thể tái lập.

- Mở lần lượt duration/RPS, số API instance, mode/algorithm, workload parameters, backend capacity.
- Thêm validate phía server, không dựa vào validate HTML phía client.
- Lưu requested config và resolved config riêng biệt.
- Hiện cấu hình sẽ chạy trước khi xác nhận bắt đầu.
- Giữ các giới hạn đã chọn qua pilot; tránh biến giá trị pilot thành ngưỡng đạt nghiên cứu.

**Tiêu chí hoàn thành:** cùng config tạo metadata rõ, có thể chạy lại bằng CLI; giá trị sai/bất khả thi bị từ chối trước khi start process.

### Giai đoạn 4 — Hoàn thiện demo và tài liệu

- Làm UI hiển thị kịch bản theo ngôn ngữ người xem: “limiter tắt”, “state cục bộ”, “state Redis dùng chung”.
- Tách KPI client hợp lệ khỏi tổng traffic và tách 429 khỏi lỗi dịch vụ.
- Ghi hướng dẫn start/stop, preset demo, giải thích số liệu, hạn chế và cách tải kết quả.
- Diễn tập demo từ trạng thái sạch và kiểm tra cleanup sau lỗi/hủy.

## 8. Quy tắc process, cleanup và an toàn

Console có quyền kích hoạt process Docker/runner nên đây là phần nhạy cảm nhất của thiết kế.

- Chỉ bind `127.0.0.1` trong bản đầu; không publish Console ra mạng ngoài.
- Chỉ gọi một danh sách script/preset cố định, dùng argv có cấu trúc.
- Không nhận shell string, path tùy ý, Docker project name hay compose file path tùy ý từ trình duyệt.
- Validate số nguyên, duration, enum, giới hạn RPS/repetitions và quan hệ giữa các tham số ở server.
- Chỉ một run hoạt động tại một thời điểm; từ chối run mới nếu project đang sở hữu container.
- Tạo folder output mới; không overwrite run cũ.
- Hủy process phải gửi signal, chờ cleanup, lưu trạng thái cleanup thành công/thất bại; không báo “canceled cleanly” khi container vẫn còn.
- Không cho tùy ý xóa artifacts hoặc đọc file ngoài thư mục artifacts.
- Giữ hành vi runner hiện hữu: project Compose riêng, refusal khi có container từ trước, timeout và cleanup do runner sở hữu.
- Không expose Redis admin, `/metrics` hay Docker socket qua UI ngoài nhu cầu local demo.

## 9. Tech stack: lựa chọn và khi nào mở rộng

### Khuyến nghị phiên bản đầu

| Lớp | Lựa chọn | Lý do |
|---|---|---|
| Backend/controller | Go hiện có | Tái sử dụng runtime và kiểu dữ liệu; quản lý process/HTTP ở cùng codebase |
| Frontend | HTML/CSS/JavaScript thuần | Một trang demo không cần dependency/build system mới |
| Experiment execution | Script runner hiện có | Đã có topology, cleanup, logging, artifact và timeout |
| Metrics demo | Poll endpoint JSON và sampling hiện hữu | Đủ cho một lượt demo local; chưa cần hệ time-series riêng |
| Output | JSON/JSONL/logs trong `artifacts/` | Tái lập và xử lý được bằng công cụ phân tích hiện tại |

### Prometheus + Grafana

Chỉ thêm khi cần dashboard time-series dùng độc lập, lưu dữ liệu qua nhiều lần chạy, truy vấn lịch sử hoặc so sánh nhiều run trong cùng giao diện. Prometheus thu thập và lưu numeric measurements theo timestamp/labels, thường scrape qua HTTP; Grafana tạo dashboard từ data sources như Prometheus. Hiện `/metrics` của project là JSON, nên để Prometheus scrape chuẩn có thể cần exposition format tương thích hoặc exporter/adapter.

Prometheus không thay thế `requests.jsonl` hay analyzer làm evidence từng request. Dùng dashboard để quan sát xu hướng; dùng artifact benchmark để phân tích correctness và quyết định quota.

- [Prometheus overview](https://prometheus.io/docs/introduction/overview/)
- [Grafana dashboards overview](https://grafana.com/docs/grafana/latest/fundamentals/dashboards-overview/)

### Loki + Alloy

Chỉ thêm nếu cần gom, tìm kiếm và đối chiếu log giữa nhiều container/run. Loki là hệ thống tập trung log; Grafana có data source Loki. Alloy có thể thu thập/đẩy log vào Loki. Stack này thêm dịch vụ, cấu hình, storage và vận hành; với log hiện đang lưu theo run, giá trị tăng thêm chưa rõ.

- [Loki data source](https://grafana.com/docs/grafana/latest/datasources/loki/)
- [Gửi log tới Loki](https://grafana.com/docs/loki/latest/send-data/)
- [Ingest logs với Alloy](https://grafana.com/docs/loki/latest/send-data/alloy/)

### Các thành phần không đề xuất ban đầu

- React/Vue/Next.js: chưa cần cho một trang nội bộ demo.
- Database: chưa cần nếu artifact trên đĩa và metadata là đủ; cân nhắc SQLite chỉ khi cần lịch sử/search trạng thái bền vững cho nhiều ngày.
- Kubernetes, distributed job queue, auth provider, Redis mới cho Console: không phục vụ nhu cầu bản local demo.

## 10. Hướng mở rộng có điều kiện

Chỉ làm sau khi Console cơ bản chạy ổn, benchmark chính thức/RQ1–RQ5 không bị ảnh hưởng và nhu cầu mở rộng đã rõ.

1. **So sánh nhiều run:** lưu registry metadata nhỏ, lọc theo config/revision và hiển thị overlay.
2. **Prometheus/Grafana:** lịch sử metrics, panel tái sử dụng, query nhiều service.
3. **Loki/Alloy:** tìm log tập trung, lọc theo run/service/instance.
4. **Metrics hệ thống rộng hơn:** container/API/Redis CPU-memory-time series đồng bộ với thời gian workload; xác nhận sampling overhead không làm sai benchmark.
5. **Outage demo:** nút kích hoạt Redis pause/unpause chỉ cho preset và thời lượng cố định, có cleanup bảo đảm; đây là thao tác fault injection nên cần xác nhận riêng trong scope demo.
6. **Export báo cáo:** tạo bundle kết quả/CSV/biểu đồ từ artifact, không sửa dữ liệu gốc.
7. **Chạy trên LAN:** chỉ khi có use case trình chiếu thật; cần bổ sung authentication, bind/firewall rõ và rà soát quyền điều khiển process trước khi mở mạng.
8. **Policy editor/management:** nằm ngoài mục tiêu Console demo và chỉ cân nhắc nếu thành câu hỏi riêng được duyệt.

## 11. Rủi ro và cách giảm

| Rủi ro | Tác động | Giảm thiểu |
|---|---|---|
| UI làm benchmark khó tái lập | Không biết run dùng config nào | Lưu requested/resolved config, revision, Run ID và artifacts |
| Controller/runner lifecycle không đồng bộ | Run treo hoặc cleanup bỏ sót | Một run một lúc; theo dõi process group; xử lý signal/timeout; kiểm tra project sau cleanup |
| Polling/metrics tạo thêm tải | Làm thay đổi latency/throughput đo được | Giữ polling nhẹ, ghi interval, so overhead có/không sampler trước khi dùng kết quả nghiên cứu |
| Dashboard diễn giải sai counter | Nhầm counter tích lũy thành delta hoặc rate | Đánh dấu nguồn, đơn vị, delta interval; đối chiếu artifact cuối lượt |
| Số liệu cuối lượt bị trình bày như live | Demo tạo hiểu nhầm | Phân biệt live samples, before/after snapshots và analyzer results |
| Cho tùy chỉnh quá nhiều biến | Vỡ ma trận, khó so sánh | Preset trước; giới hạn biến theo RQ; lưu mọi config |
| Bổ sung Grafana/Loki quá sớm | Thêm thời gian triển khai và vận hành | Chỉ thêm theo nhu cầu quan sát đã xác nhận |
| Console lộ ra mạng | Người khác có thể khởi chạy workload hoặc đọc log | Loopback-only bản đầu; không arbitrary commands/paths; rà soát riêng trước khi bind LAN |

## 12. Tiêu chí quyết định tiếp tục

Console đáng triển khai nếu đáp ứng các điều kiện sau:

- Có kịch bản demo cụ thể mà CLI đang gây cản trở.
- Giao diện giúp giải thích trực tiếp một hoặc nhiều kết quả liên quan đến RQ, thay vì chỉ thêm màn hình.
- Có thời gian sau khi protocol, dữ liệu benchmark và báo cáo bản đầu đã đủ an toàn.
- Có thể giữ runner hiện có làm nguồn thực thi chuẩn và tạo artifacts tương đương CLI.
- Người học có thể giải thích từng metric và giới hạn của kết luận trong buổi bảo vệ.

Nếu cần cắt scope, giữ read-only demo view hoặc chỉ một preset Run; bỏ Grafana/Loki, history database, policy editor và arbitrary benchmark matrix.

## 13. Câu hỏi cần chốt trước khi code

1. “Option B” đã loại bỏ cụ thể là gì, và phần demo console có được xem là một lát của phương án đó không?
2. UI chỉ dùng trong demo trên laptop hay cần truy cập từ thiết bị khác trong LAN?
3. Kịch bản trình diễn chính là mixed traffic, burst/concurrency, scaling hay Redis outage?
4. Có cần chỉnh benchmark tùy ý hay chỉ chọn preset và vài giới hạn đã định?
5. Giao diện cần live metrics nào là bắt buộc; metrics nào có thể chỉ hiện sau khi run kết thúc?
6. Ưu tiên hoàn thành benchmark/báo cáo trước rồi mới làm Console, hay Console là deliverable demo được duyệt sớm?

## 14. Kết luận

Phương án hợp lý nhất để bắt đầu là Go + HTML/JavaScript thuần + runner hiện có + artifact JSON/JSONL. Bắt đầu bằng trang read-only để xác nhận metrics và cách kể demo; sau đó thêm điều khiển một preset benchmark, rồi mới mở thêm tham số có validate. Prometheus/Grafana là lựa chọn cho time-series dashboard dài hạn; Loki/Alloy là lựa chọn tập trung log. Cả hai đều là phần mở rộng, không phải phụ thuộc bắt buộc để có UI demo.

Ranh giới này biến thao tác demo hiện tại thành trực quan hơn nhưng vẫn giữ công cụ benchmark và dữ liệu có thể tái lập làm nguồn chính.
