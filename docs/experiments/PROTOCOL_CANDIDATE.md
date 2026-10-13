# Protocol nghiên cứu ứng viên — 13/10/2026

**Chưa được duyệt, chưa khóa, chưa chạy bộ đo theo tài liệu này.** Mọi số dưới đây là đề xuất để hiệu chỉnh trên máy đo; không phải yêu cầu nguồn hay tham số benchmark đã chọn. Tài liệu bổ sung [pilot hiện có](PILOT_PROTOCOL.md), không thay [đặc tả](EXPERIMENT_SPEC.md) hoặc lịch đề xuất.

## Cơ sở và giới hạn

**Yêu cầu dự án:** theo [Roadmap](../context/sources/00_Project3_Roadmap.md) trước [Proposal](../context/sources/01_Project3_Proposal.md), trả lời RQ1–RQ5 bằng so FW/TB, local/Redis, một/nhiều API, concurrent atomicity, mixed backend protection và outage Redis có giới hạn. Đo correctness, latency, throughput, Redis CPU/memory, goodput hợp lệ, backend arrivals, 429/timeout/5xx, availability và recovery. Nguồn không chốt tải, thời lượng hay số lần lặp.

**Lựa chọn kỹ thuật hiện có:** middleware API trước backend chung, local mutex/Redis Lua, quota theo key, thời gian millisecond và fail-open/closed trong [IMPLEMENTATION](../IMPLEMENTATION.md). Roadmap và Proposal minh họa vị trí limiter khác nhau; lựa chọn prototype không sửa khác biệt nguồn. Tài liệu nguồn local đủ để đề xuất phương pháp này; không cần reconnect Drive để lặp lại ngữ cảnh.

**Khuyến nghị kỹ thuật:** các ma trận, ngưỡng chất lượng và quy trình bên dưới. **Tùy chọn tương lai:** Sliding Window, Redis Functions, dashboard/monitoring nâng cao. Không thêm gateway, Redis Cluster/HA, Kubernetes, xác thực hay dịch vụ bán hàng.

Flash sale giả định → traffic bất thường làm backend chậm/lỗi → người mua hợp lệ mất khả năng giao dịch → cần quota chung và kiểm soát tải trước backend → so limiter bằng phép đo có đối chứng → đánh giá trade-off → ghi giới hạn/hướng phát triển; không quy goodput mô phỏng thành doanh thu thực tế.

## Điều kiện trước khi khóa

Giữ nguyên [84 lượt pilot](../worklog/2026-10-12-console-matrix/README.md): **2 local TB oracle mismatches, 19 Redis limiter errors, 5 generator drops và 40 inconclusive** là kết quả lịch sử. [Điều tra TB ngày 13/10](../worklog/2026-10-13-token-bucket/README.md) xác nhận lỗi float tại biên refill và bổ sung sửa lỗi/regression; chưa pilot lại HTTP sau sửa. Redis timeout, drops và giới hạn inconclusive vẫn còn mở. Không đổi `completed` thành correctness pass. Điều tra timeout bằng logs/counters mọi API; drops bằng lịch gửi/inflight/tài nguyên. Mismatch expected allow/observed reject là under-admission trong hai trace, không phải overshoot. Lưu lý do và revision sửa code/oracle, phân tích bản sao artifact và pilot lại các nhóm bị ảnh hưởng trước khóa.

Hiệu chỉnh baseline dưới quota: `normal` chỉ là nhãn toàn traffic hợp lệ; pilot cũ 120/5 = 24 RPS/key vượt 20/key/s. Ứng viên mới: tổng 20 RPS hợp lệ/5 key với `Q=20,W=1s,B=20,r=20/s`, backend không quá tải. Xác nhận tải từng key, không chỉ trung bình, nằm dưới cấp phát; 429 ngoài kỳ vọng phải điều tra.

Hiệu chỉnh mixed bằng **no limiter trước**, đề xuất tổng 120 RPS = 20 hợp lệ + 100 bất thường, backend capacity4/service50ms. Đây là điểm bắt đầu từ pilot vòng 2, không bảo đảm overload trên máy mới. Phải có arrivals/overload đo được và goodput/tail hợp lệ suy giảm so normal, generator vẫn đạt tải. Sau đó giữ đúng backend/tải ấy cho local/Redis; không điều chỉnh riêng từng mode để tạo kết quả thuận lợi.

## Ma trận nhỏ, có đối chứng

| Nhóm | Biến thay đổi, biến giữ nguyên | Bằng chứng/RQ |
| --- | --- | --- |
| Normal + burst | FW/TB × local/Redis tại 2 API; thêm none dùng chung mỗi workload. Giữ key, policy rate, backend, lịch gửi. Burst đề xuất nền 20 hợp lệ + 20 bất thường, tăng bất thường lên 200 RPS trong giây 10–12 của lượt 30s. | RQ1/RQ2: allow/reject, burst, latency từng class/decision, throughput và Redis resource. Burst gần biên FW cần xác minh server window riêng; runner hiện không khóa pha vào biên. |
| Mixed overload | none, local FW, Redis FW tại 2 API; lặp local TB/Redis TB trên cùng tải/backend, không nhân nhãn algorithm cho none. | RQ5 và RQ1/RQ2: legitimate goodput/p95/p99, backend arrivals/success/overload/canceled và 429/timeout/5xx. |
| Scaling sweep | 1/2/4 API × none/local/Redis FW; tối thiểu 3 mức offered load chung đã hiệu chỉnh: dưới ngưỡng, gần ngưỡng, trên ngưỡng. Giữ backend, policy, key distribution và resource budget từng API. | RQ3: đồ thị tải → throughput/tail/quota; Redis CPU/memory, generator/API/LB/backend bottleneck. Chọn tải theo pilot rồi khóa cùng mức cho mọi topology. |
| Concurrent | Local/Redis atomic FW và TB tại 2 API, cùng key, batch đề xuất 100 request tại giây 2; kiểm tra thời điểm gửi/decision thực. Thêm bài test Redis thật atomic và non-atomic control hiện có. | RQ4: quota/envelope, quyết định oracle, log test concurrency; local nhiều instance vượt quota chung là state isolation, không phải bằng chứng Redis race. |
| Outage riêng | Redis FW, open/closed trên cùng workload/topology/backend; thêm Redis khỏe không outage cùng policy làm baseline. TB outage là nhóm bổ sung nếu cần kết luận cho TB. | RQ5: availability hợp lệ, quota/fallback, latency và recovery theo pha. Không gộp với scaling. |

`B=Q,r=Q/W` chỉ ghép tốc độ dài hạn: TB đầy ban đầu/refill liên tục, FW reset theo epoch; không tương đương burst hoặc tổng allowed. Local mỗi instance giữ nguyên Q/B để đo tác động state; quota hiệu dụng tăng theo routing. Không chia Q cho N rồi gọi là cùng phép so state. None là chi phí đường đi/backend; không có oracle quota.

Scaling cần workload key distribution cho phép tăng **accepted work**, không chỉ tăng 429 trên một key quota cố định. Với giới hạn custom 5 legitimate keys/1 abusive key, phải ghi rõ quota có chặn throughput hay không; nếu không tạo được vùng tải API chịu áp lực mà backend/generator còn ổn, chỉ kết luận scaling trong vùng đo được. Backend chung trên một host là giới hạn cố ý: sweep không tự chứng minh mở rộng tuyến tính hoặc production scalability.

Concurrent batch hiện bắt đầu state mới, chưa preconsume quota gần cạn. Kiểm tra quota gần hết bằng integration test nhỏ; không mô tả runner như đã hỗ trợ pha prefill. Non-atomic barrier chỉ trong test, minh họa lost update có kiểm soát; không suy tần suất race tự nhiên hoặc so hiệu năng HTTP với Lua từ bài này. Khóa trước việc RQ4 dùng bằng chứng bất biến + control test, hay cần thêm đối chứng cùng harness gần cạn; nếu chọn vế sau, đó là việc còn thiếu.

## Thời gian, reset và lặp đề xuất

Chọn **3 lượt độc lập/cell, 30s offered load/lượt** cho normal/burst/mixed/scaling; concurrent 6s với batch hữu hạn. Nếu pilot cho p99 thiếu mẫu/dao động lớn, chọn lại số lượt/thời lượng trước đo chính thức; không tăng riêng nhóm có kết quả xấu. Báo median và min–max các chỉ số từng lượt; 3 lượt chưa đủ để khẳng định ý nghĩa thống kê. Không gộp percentile hay lấy trung bình p95 rồi gọi là p95 toàn bộ.

Runner hiện đợi **1s sau health check, không gửi tải warm-up**. Đề xuất dùng đúng chế độ khởi đầu lạnh này và ghi rõ; không gọi 1s là warm-up. Phân biệt phase đầu/steady trong trace nếu phân tích thêm, không bỏ request đầu khỏi oracle. Nếu muốn warm-up có tải, phải định nghĩa thời lượng/key/state/reset/metric boundary trước và bổ sung harness; hiện chưa có.

Mỗi lượt: fresh containers/local processes và namespace Redis riêng, bucket đầy, không `FLUSHDB`; ghi `state_reset`, policy thực, revision/dirty tree, image ID, môi trường CPU/RAM/Docker, timeout/inflight, lịch tải, clocks, mọi snapshots/logs/trace. Không chạy các case đồng thời. Đổi thứ tự mode/topology theo block lượt lặp có seed hoặc lịch cố định đã lưu để giảm bias do thứ tự; built-in runner hiện luôn theo thứ tự case, nên custom cell riêng phù hợp hơn. Đợi host về mức nhàn đã hiệu chỉnh trước cell tiếp; ghi thời gian nghỉ, không chọn theo kết quả.

## Quy tắc validity/exclusion phải khóa trước đo

- Artifact đủ, unique request IDs, policy/metadata đúng, raw/summary reconcile, backend/API counters mọi instance đầy đủ; health/reset/clock ổn định. Analyzer process thành công chưa đồng nghĩa oracle pass.
- Ứng viên fidelity: **0 drops**, tổng sent bằng scheduled; offered RPS thực trong ±5% mục tiêu cho từng pha/class; p95 schedule lag ≤10ms và ≤một khoảng gửi của luồng tương ứng. Concurrent báo send spread riêng, không áp RPS trung bình; đề xuất ≥90% batch được gửi trong một W, đồng thời phải kiểm tra decisions không straddle FW boundary khi dùng count quota. Hiệu chỉnh các ngưỡng này trước khóa, không nới sau khi thấy kết quả.
- Redis errors/fallback bất ngờ trong nhóm healthy: không dùng để kết luận overhead/correctness khỏe; giữ như kết quả lỗi và điều tra. Backend overload chủ ý trong mixed/scaling trên ngưỡng, và fallback chủ ý trong outage **là outcome**, không phải lý do loại vì làm xấu số đo. Transport timeout có thể là outcome overload nhưng khiến replay key tương ứng inconclusive; không tự loại toàn lượt hoặc gọi là quota pass.
- Oracle violation có evidence đủ là kết quả cần báo, không loại chỉ vì sai. Inconclusive không pass; FW trace hiện chỉ cho lower-bound overshoot/observed decisions, không chứng minh cửa sổ đầy đủ. TB cần state ban đầu, decisions đầy đủ và timestamps hợp lệ; không dùng quota FW đánh giá TB.
- Lượt thiếu evidence hoặc generator không đạt tải bị loại **chỉ khỏi phép so sánh liên quan**, giữ run_id/lý do; chạy lại cùng cell, không ghi đè. Đề xuất tối đa 2 lần thử thay thế/cell; nếu vẫn không đạt, dừng nhóm và báo chưa đo được. Không âm thầm thay tải/protocol trong bộ chính thức.

## Outage và tiêu chí recovery đề xuất trước đo

Harness hiện là `redis-outage.sh`: hai API, 10s offered load, tổng100/legitimate20 RPS, pause Redis sau khoảng3s trong2s, chạy open rồi closed; dùng policy/backend Compose đã resolve. Các số này chỉ là smoke candidate. Lặp bằng output riêng cho từng lượt; tránh chạy trùng project. Pause giữ state Redis, không mô phỏng restart/data loss hoặc production HA.

Ghi đủ `pause_requested/completed`, `unpause_requested/completed`; tách transition khỏi pre/during/post. Dùng timestamps thực, không coi sleep là outage thực chính xác. Healthy baseline phải giữ workload/backend/topology/policy ấy. Nếu 10s không đủ full post windows sau control-plane delay, recovery inconclusive; chọn harness dài hơn trước bộ chính thức, không lấy response drain làm thời gian offered load.

Đề xuất khóa analyzer recovery window=1000ms, min legitimate samples=5/window, consecutive=3; threshold p95 = **1,5 × median legitimate p95 của healthy calibration tương ứng** (giá trị ms phải ghi vào manifest trước đo). Một window recovery phải đầy đủ, sạch fallback/error và đủ mẫu; không đủ thì `null/inconclusive`. Báo thời gian từ unpause_completed đến stable recovery, first success riêng và độ phân giải window. Không chọn threshold bằng dữ liệu outage chính thức.

Availability = legitimate 2xx / legitimate sent từng pha; ghi cả scheduled/dropped để không che thiếu tải. Quota fail-open: fallback có thể vượt quota do policy; timeout cũng có thể đã đổi Redis state nên không replay chính xác. FW báo observed lower-bound/global allows; TB báo envelope nếu đủ time/state, nếu không ghi unknown/inconclusive. Không khẳng định fail-closed giữ quota tuyệt đối khi thiếu response/state evidence; tách quota policy khỏi backend success. Outage bounded này chỉ trả lời trade-off trong môi trường đo.

## Công cụ dùng được và lựa chọn còn mở

`research-pilot.sh --case custom` đã hỗ trợ 1/2/4 API, FW/TB, none/local/Redis, duration3–30s, RPS≤1000, policy/backend/profile; repetitions1–3, 5 legitimate keys, inflight200/timeout2s cố định. Dùng [scripts/README](../../scripts/README.md) và resolved config, không suy nhãn generator thành server state. `--analyze` dùng mặc định chưa có threshold recovery; outage cần gọi analyzer riêng với các cờ trong [ANALYSIS](ANALYSIS.md). Built-in scale cases giữ 100 RPS, không thay sweep đề xuất; không có runner cho Redis non-atomic HTTP hoặc burst đồng bộ biên.

Trước khóa cần người dùng/nghiên cứu quyết định: Q/W/B/r và tải sau calibration; mức sweep có quota headroom; cold-start hay bổ sung warm-up; 3×30s có đủ mẫu không; các ngưỡng fidelity/recovery; cách trả lời RQ4 và có cần TB outage; tiêu chí full-window/unknown state; resource budget/topology và thứ tự chạy. Giải thích cả lý do chọn và giới hạn. Sau đó lưu protocol version/manifest, chạy chính thức, đánh giá từng RQ với biến thiên và các lượt bị loại; hiện chưa có kết luận thuật toán hoặc fail policy tốt hơn.
