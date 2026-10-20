# Công việc còn lại và kế hoạch tiếp tục Project 3

**Kế hoạch gốc 13/10/2026; cập nhật trạng thái 20/10/2026.** T01–T08 đã hoàn tất trong giới hạn đã ghi. T09 đã hoàn tất đo sau một lượt v1.3 được người dùng cho phép để bổ sung ô v1.2 còn thiếu duy nhất. Checker đạt (7.500/7.500 request đã gửi, không rơi request, 250 RPS, fingerprint khớp); dữ liệu dẫn xuất đã sửa có 138/138 vị trí chạy dự kiến dùng được, tổng hợp 46/46 cấu hình, gồm cả bốn cấu hình outage. Manifest v1.2 và bằng chứng trước đó không đổi. Xem [phụ lục v1.3](experiments/protocol-v1.3/protocol.md); gói bàn giao archive/checksum đã hoàn tất tại [bằng chứng v1.3](worklog/2026-10-20-t09-v1.3/README.md) và [checksums](worklog/2026-10-20-t09-v1.3/SHA256SUMS). SHA-256 archive `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`; giải nén, kiểm tra checksum và dọn dẹp đều đạt. T10 chưa bắt đầu; chưa có kết luận RQ. Không chạy thêm tải; dừng trước T10. Các giới hạn về độ chính xác UTC/độ bền sau khởi động lại, backend mô phỏng và network counter tổng của T08 vẫn còn. Các dependency và quality gate được giữ nguyên; phần học do người dùng thực hiện với GPT. Đây là danh sách phần việc còn lại đã biết về nghiên cứu, mã đo lường, tài liệu, demo và việc người học cần làm. Người dùng chọn mốc nộp tạm **giữa tháng 12/2026** ngày 19/10; ngày nộp/bảo vệ chính thức, rubric và phản hồi tiếp theo của giảng viên chưa xác định đầy đủ, nên có thể phát sinh điều chỉnh. Không dùng số lượng checkbox để suy phần trăm hoàn thành.

Nguồn yêu cầu: [Roadmap](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md). Kế hoạch đo v1.2 đã khóa là protocol kỹ thuật, không phải yêu cầu được giảng viên phê duyệt; các ví dụ khác dưới đây chỉ để lập kế hoạch, trừ khi v1.2 quy định khác. [Checkpoint](context/SESSION_CHECKPOINT.md) ghi phần đã xong; [readiness](experiments/PROTOCOL_READINESS.md) ghi điều kiện chưa đạt.

**Trạng thái lịch sử trước khi tiếp tục T09 (19/10):** T04 có 10 lượt normal/burst đạt quality; T05 có 27 cấu hình hợp lệ; T06 có các bài test Redis; T07 có bốn ca healthy/outage capacity10 và exporter smoke; T08 kiểm chứng sampler và khóa protocol v1. Việc dừng trước T09 khi đó là thông tin lịch sử; phép đo T09 hiện đã hoàn tất như ghi dưới đây. Xem [worklog T08](worklog/2026-10-19-t08-network/README.md).

**Cập nhật gate lịch sử (19/10):** T01 ổn định clock trong phiên, T02 vòng đời observer/runner/checker và gate normal/mixed có giới hạn của T03 đều đạt trong phạm vi ghi nhận. Độ chính xác UTC và độ bền sau restart/resume chưa được xác minh; oracle Fixed Window chưa kết luận được. T11 có bản nháp báo cáo; T12 đã chuẩn bị demo từ lượt đã lưu. Trạng thái chính thức hiện tại ghi ở phần trên và [checkpoint](context/SESSION_CHECKPOINT.md).

## 1. Những phần đã xong, không cần làm lại

- Prototype Go/API/backend/LB, local và Redis Lua cho FW/TB, topology 1/2/4, generator và analyzer đã có.
- Lỗi float local TB và deadline Redis đã có sửa/test/evidence; không cần điều tra lại từ đầu nếu không có finding mới.
- Console chọn lượt, hiển thị chất lượng và so sánh runtime content đã kiểm tra trên Docker thật và desktop/mobile.
- Đã có archive/checksum, exporter CSV/Markdown, hình pilot và kịch bản demo. Kiểm tra cuối đã đạt; không chạy lại toàn suite chỉ để bắt đầu phiên.
- Bối cảnh doanh nghiệp flash sale giả định đã chọn. Không mở lại lựa chọn stack/kiến trúc hoặc biến đồ án thành gateway/HA.

**Trạng thái gate:** các gate T02/T03 trước đó đạt trong giới hạn đã ghi. T09 v1.2 và lượt v1.3 bổ sung một vị trí chạy dự kiến đều qua observer mới 90 giây trước khi tạo tải (không có bước nhảy trên 5 ms). Dữ liệu dẫn xuất T09 hoàn tất ở mức 138/138; độ chính xác UTC và độ bền clock sau restart/resume chưa xác minh. T10 và kết luận RQ chưa bắt đầu.

## 2. Toàn bộ todo theo thứ tự phụ thuộc

| ID | Công việc còn lại | Phụ thuộc | Đầu ra / điều kiện hoàn thành |
| --- | --- | --- | --- |
| T01 | Xác định môi trường có clock ổn định; chẩn đoán read-only hoặc chuyển máy/môi trường đo | Không | **Đạt ổn định trong phiên hiện tại:** observer 90 giây sau remediation không ghi nhận step >5 ms. Độ chính xác UTC tuyệt đối (Windows lệch khoảng 4,05 giây) và độ bền sau restart/resume chưa xác minh. Live gate T02/T03 hoàn tất như [worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T02 | Chuẩn bị observer/gate tái chạy được, không phụ thuộc `/tmp` phiên cũ | Không, có thể chuẩn bị trước T01 | **Hoàn tất:** observer 90 giây mới và live runner/checker lifecycle tại revision cố định; raw output/checksum trong [T02/T03 worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T03 | Chạy lại gate normal/mixed sau sửa, kiểm chứng generator/clock/healthy Redis | T01–T02 | **Hoàn tất pilot gate:** 3 normal + 3 mixed × 30 giây đạt mọi quality check, không có drop. Oracle FW `inconclusive`; đây không phải correctness pass hoặc benchmark chính thức. |
| T04 | Hiệu chỉnh phép so normal/burst FW/TB × local/Redis và baseline none | T03 | **Hoàn tất calibration có giới hạn:** 10 cấu hình × 1 lượt × 30 giây, 10.800 sent=scheduled, không drop/quality flag; cùng policy rate, workload/key/backend/topology, đã kiểm tra từng pha/class. Xem [T04 worklog](worklog/2026-10-19-calibration-next/README.md). FW inconclusive, một lượt không đủ kết luận so sánh hiệu năng; B=Q,r=Q/W không đồng nhất burst semantics. |
| T05 | Hiệu chỉnh scaling 1/2/4 với tải dưới/gần/trên ngưỡng | T03 | **Hoàn tất calibration có giới hạn:** 27 cấu hình hợp lệ × 10 giây, 43.200 sent, không drop/quality flag trong các lượt hợp lệ; quota headroom, một replacement cùng cấu hình, giữ một lượt drop và ba lượt gián đoạn. Backend chung giới hạn khoảng 190 success/s ở 250 RPS; chưa chứng minh API scaling hoặc mode tốt hơn. [T05 worklog](worklog/2026-10-19-calibration-next/T05-README.md). |
| T06 | Chốt bằng chứng concurrent/atomicity cho RQ4, gồm quota gần cạn | T03 | **Hoàn tất bằng chứng test có giới hạn:** shared quota và quota gần cạn FW/TB đạt trên Redis thật, kèm đối chứng non-atomic ép race; xem [T06 worklog](worklog/2026-10-19-atomicity/README.md). Không suy tần suất race tự nhiên hoặc hiệu năng HTTP từ test. |
| T07 | Hoàn thiện schema/lifecycle runner outage và hiệu chỉnh recovery | T03 | **Hoàn tất bounded calibration:** 4 cases × 30s, 12.000 sent=scheduled, zero drops, healthy gates đạt; stable recovery 4s theo 1s/min5/3 windows, first success riêng. Exporter smoke 4/4 usable sau fix null resources riêng; FW vẫn inconclusive. [T07 recovery](worklog/2026-10-19-outage-recovery/README.md). |
| T08 | Khóa protocol và manifest phiên bản cụ thể | T04–T07 | **Hoàn tất có giới hạn:** kiểm chứng sampler trực tiếp và khóa protocol v1 được ghi trong [worklog](worklog/2026-10-19-t08-network/README.md), [protocol](experiments/protocol-v1/protocol.md) và [manifest](experiments/protocol-v1/manifest.json). Chưa chạy benchmark chính thức. |
| T09 | Chạy benchmark chính thức tuần tự và khóa dữ liệu | T08 | **Hoàn tất.** Một lượt v1.3 được người dùng cho phép đã bổ sung ô v1.2 còn thiếu duy nhất. Checker đã khóa đạt: 7.500/7.500 request đã gửi, không rơi request, 250 RPS, fingerprint khớp. Export dữ liệu dẫn xuất đã sửa: 138/138 vị trí chạy dự kiến dùng được, tổng hợp 46/46 cấu hình, gồm cả bốn cấu hình outage. Manifest v1.2 và bằng chứng trước đó không đổi. Xem [phụ lục v1.3](experiments/protocol-v1.3/protocol.md), [bàn giao bằng chứng](worklog/2026-10-20-t09-v1.3/README.md) và [checksums](worklog/2026-10-20-t09-v1.3/SHA256SUMS); SHA-256 archive `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`, giải nén/checksum/dọn dẹp đều đã xác minh. Không chạy thêm tải; dừng trước T10. |
| T10 | Phân tích và xuất bảng/hình trả lời RQ1–RQ5 | T09 | **Chưa bắt đầu.** Cần bộ dữ liệu T09 đầy đủ được chấp nhận và chỉ dẫn riêng của người dùng. Chưa phân tích hoặc kết luận RQ. |
| T11 | Hoàn thiện báo cáo và sửa theo phản hồi giảng viên | Khung có thể viết ngay; kết quả đợi T10 | Bối cảnh → pain point → tác động → yêu cầu → giải pháp → thí nghiệm → đánh giá → phát triển tương lai; không quy mô phỏng thành doanh thu thật. |
| T12 | Đóng gói demo/source, restore saved runs và thử clean checkout | Có thể chuẩn bị ngay; bản cuối đợi T09–T10 | Lệnh chạy/reproduce, saved UI và offline fallback; không overwrite artifacts; report/slide/demo cùng phiên bản bộ nộp cuối. |
| T13 | Hoàn thiện slide, diễn tập và bộ nộp | T10–T12 | Slide/demo có thời lượng, hỏi đáp, phương án mất Docker/internet, định dạng/hạn nộp đúng; commit/tag cuối và worktree sạch. |
| H01 | Tự kiểm tra kiến thức nền/thuật toán/phương pháp đo | Song song mọi giai đoạn | Người học tự giải thích/tính tay; AI không tự đánh dấu đã hiểu. Dùng câu hỏi trong PROJECT_ROADMAP và DEMO_SCRIPT. |
| H02 | Xác nhận ngày nộp/bảo vệ, rubric và yêu cầu hình thức với giảng viên | Song song; cần người học | Cập nhật kế hoạch khi có thông tin, không tự gửi email/tin nhắn hoặc suy rubric từ tài liệu dự án. |

Các tính năng Sliding Window, dashboard lớn, xác thực/RBAC, Redis Cluster, Kubernetes, gateway và framework frontend bổ sung là **tùy chọn/ngoài phạm vi**, không thuộc danh sách việc cần hoàn tất cho baseline. Lỗi mới ảnh hưởng tính hợp lệ/tính đúng là việc cần xử lý khi phát sinh, không phải lý do tự mở rộng tính năng.

## 3. Cách triển khai các phần kỹ thuật còn mở

### T01–T03: clock và gate

Tái dùng [observer](worklog/2026-10-13-clock/observe.py), [PRESET](worklog/2026-10-13-postfix/PRESET.md) và [quality checker](worklog/2026-10-13-postfix/check-quality.py). Observer archival có đường dẫn `/tmp/project3-clock-observer` cố định; [run-gate](worklog/2026-10-13-postfix/run-gate.sh) còn gọi `/tmp/postfix-quality.py` và output cũ. Chúng là evidence cách chạy trước đây, **không chạy nguyên bản như portable runner**. Phiên tiếp theo sửa bản helper tối thiểu để lấy checker từ repo và dùng output mới; helper mới/sửa có self-check hoặc focused test, không thay raw archival.

Gate chạy từng lượt (`--repetitions 1`), kiểm tra chất lượng rồi mới chạy lượt sau; theo dõi điều kiện chặn qua các lượt. Lệnh `--repetitions 3` hiện không tự kiểm tra chất lượng giữa các lượt để dừng sớm. Gate dự kiến giữ Q=B=20,W=1000ms,r=20/s; 2 API, 5 key client hợp lệ, backend capacity4/service50ms; normal20 RPS, mixed120/20; request/dial/pool100ms, generator2s/inflight200; sau health 1 giây không tải thì bắt đầu đo.

Điều kiện đã đặt: 0 drops, raw/summary/counters reconcile, không healthy Redis errors, offered rate từng pha/class ±5%, p95 lag ≤10ms và ≤send interval; wall–monotonic residual cả scheduling và response latency ≤5ms. Normal không reject/overload. Overload chủ ý trong mixed và fallback chủ ý trong outage là outcome. FW partial-window `inconclusive` không tự làm lượt invalid, nhưng không là correctness pass. Không tăng ngưỡng clock hoặc sửa timestamp để che step.

### T04–T07: calibration và bằng chứng đã hoàn tất

**T04/T05 đã hoàn tất calibration, T06 đã chốt bằng chứng tests:** không chạy lại nếu không có finding/đổi code liên quan. T04/T05 đã tái dùng `research-pilot.sh --case custom`: topology1/2/4, duration3–30s, repetitions1–3, RPS≤1000 và 5 legitimate keys. Nếu giới hạn quota/key/backend chặn phép đo scaling, ghi lại và thiết kế workload headroom trước; không mở tải/config tùy ý chỉ để benchmark trông mạnh hơn. Burst sát biên FW chưa được runner đồng bộ server window; chỉ bổ sung nếu kết luận cần thí nghiệm đó.

T06: tests Redis thật có Lua atomic và non-atomic control; batch HTTP hiện chưa có phase preconsume quota. Đã chọn bằng chứng invariants + tests quota gần cạn FW/TB, không thêm non-atomic HTTP service. Control có barrier chỉ chứng minh tình huống race được tạo, không suy tần suất race tự nhiên hoặc so performance HTTP từ test.

T07: [redis-outage.sh](../scripts/redis-outage.sh) đã có policy/resolved JSON, counters trước/sau mọi API/backend, revision/images/inspect, unique IDs, parent metadata và analysis cho cả healthy/outage. Startup/cleanup hữu hạn và healthy gate có 4 mocks. Live capacity10/50ms, 100/20 RPS, 30s, pause4s/2s đã hoàn tất trên checkout sạch; recovery ổn định 4s theo tiêu chí cửa sổ, exporter smoke 4 cases usable. Null-resource exporter fix có 7 regression tests. Batch capacity4 overload/dirty status vẫn là evidence lịch sử, không sửa metadata cũ. Xem [worklog](worklog/2026-10-19-outage-recovery/README.md); không chạy lại khi chưa có finding mới.

Outage cần lượt nền healthy với cùng mẫu tải/backend/topology/policy; ghi thời điểm yêu cầu và hoàn tất pause/unpause, tách giai đoạn chuyển trạng thái; chọn thời lượng đủ cho các cửa sổ đo sau sự cố. Tiêu chí recovery dự kiến là cửa sổ 1s, tối thiểu 5 mẫu client hợp lệ, 3 cửa sổ liên tiếp và ngưỡng lấy từ hiệu chỉnh healthy được ghi trước khi đo. Chỉ thêm outage Token Bucket nếu cần kết luận riêng về thuật toán này. Không biến việc pause Redis thành nghiên cứu HA, restart hay mất dữ liệu. Khi thiếu response/state, chỉ báo quota vi phạm là cận dưới hoặc chưa rõ; không kết luận đạt tuyệt đối.

Nếu request bị rơi tái diễn khi clock ổn định, hãy so sánh sampler bật/tắt ở cùng mức tải trước khi sửa scheduler. Giữ cơ chế loại lịch gửi đã lỗi thời; không tăng timeout hoặc hạ tải chỉ để xóa cờ cảnh báo. Proposal có đề cập overhead mạng. T08 đã kiểm chứng trong giới hạn các bộ đếm delta/đơn vị/lấy mẫu mạng Redis; khi báo cáo, ghi tổng lưu lượng Redis cùng lưu ý về sampler, thao tác quản trị, health check và mẫu tải. Không quy thành byte/request chỉ của limiter và không tuyên bố đã hiệu chỉnh overhead.

### T08–T10: protocol, thực chạy và đánh giá

T08 đã hoàn tất. Protocol v1 và v1.1 là phiên bản lịch sử; T09 dùng [protocol v1.2](experiments/protocol-v1.2/protocol.md) và [manifest](experiments/protocol-v1.2/manifest.json) đã khóa, giữ ma trận 46 cấu hình/138 vị trí chạy dự kiến và các ngưỡng. [Phụ lục v1.3](experiments/protocol-v1.3/protocol.md) được cho phép để bổ sung đúng vị trí chạy dự kiến trước đó còn thiếu và đã đạt; xem [bằng chứng v1.3](worklog/2026-10-20-t09-v1.3/README.md) và [checksums](worklog/2026-10-20-t09-v1.3/SHA256SUMS), SHA-256 archive `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`; giải nén/checksum/dọn dẹp đều đạt. Kiểm chứng sampler trực tiếp được ghi trong [worklog T08](worklog/2026-10-19-t08-network/README.md). Phép đo T09 hoàn tất với 138/138 vị trí chạy dự kiến dùng được và 46/46 cấu hình tổng hợp. Không chạy thêm tải; dừng trước T10. Không lặp pilot đã hoàn tất nếu chưa có finding liên quan.

Manifest v1.2 liệt kê rõ các cấu hình cần chạy, ánh xạ RQ, số lần lặp, cấu hình, thứ tự chạy, tài nguyên, độ trung thực, clock, quy tắc lượt không hợp lệ/thay thế và recovery. Ma trận đã khóa gồm 46 cấu hình, khác với ma trận trong bản nháp trước đó. Ghi chú cũ `3×30s` chỉ là phương án dự kiến, không phải yêu cầu được phê duyệt. Mọi thay đổi về sau cần có lý do và phiên bản riêng; không âm thầm gộp kết quả giữa các phiên bản.

Exporter hiện kiểm tra tính nhất quán **trong từng cấu hình**, nhưng không tự chứng minh hai cấu hình là một phép so sánh có kiểm soát. Người phân tích phải đối chiếu các yếu tố giữ cố định: mẫu tải, key, thuật toán, state, topology, backend, revision và nội dung runtime. Báo cáo median và min–max của metric theo từng lượt, giữ lại mọi lượt không hợp lệ, không gọi median của p95 là p95 gộp. Các khẳng định về Lua/race, goodput/đuôi độ trễ của client hợp lệ, kết quả backend, CPU core/bộ nhớ/network Redis nếu có, availability/recovery khi outage đều cần bằng chứng tương ứng; không mặc định exporter đã xuất mọi biểu đồ/metric cuối.

`plot-calibration.py` hiện chỉ vẽ pilot mixed từ cấu trúc JSON của calibration, chưa phải quy trình vẽ cuối cho mọi RQ. Khi T10 được tiếp tục riêng, mới tạo biểu đồ thuật toán/scaling/atomicity/outage từ dữ liệu đo thật bằng công cụ vẽ thông dụng; Matplotlib chạy ngoại tuyến và không phải dependency của Go/runtime. Bộ biểu đồ/bảng cuối cần kèm manifest, nguồn dữ liệu, chú thích, giới hạn và phiên bản; không dùng biểu đồ pilot làm số liệu chính thức.

### T11–T13 và H01–H02: sản phẩm để nộp

Khung báo cáo và phần nền có thể viết khi clock chưa ổn định. Chương kết quả, kết luận và slide có kết quả chờ T10. Cần tài liệu liên quan/trích dẫn phù hợp, giải thích policy/thời gian/tính nguyên tử/fail policy, mô tả máy đo và nguy cơ ảnh hưởng tính hợp lệ, phản hồi giảng viên và định dạng theo rubric khi có; không tạo nguồn trích dẫn hoặc số liệu giả.

Đóng gói demo theo [DEMO_SCRIPT](DEMO_SCRIPT.md). Các lượt đã lưu cuối cùng nằm trong archive [Console content](worklog/2026-10-13-console-content/README.md), trong thư mục có tiền tố theo mode; controller chỉ nạp `artifacts/console/<status.id>/status.json`. Khôi phục nguyên thư mục theo ID gốc vào một thư mục chưa tồn tại; không sửa metadata/checksum. Phải giữ cờ clock của lượt local. Các hình hiện tại lấy từ calibration cũ, không ghép số liệu/revision với bộ ba lượt Console cuối. Bản nộp cuối dùng thống nhất phiên bản code/protocol/dataset, có demo dự phòng ngoại tuyến và lệnh tái tạo đã thử trên checkout sạch.

H01 gồm tự tính FW/TB/burst/refill, quota local trên N instance, Lua atomic/race, 429 so với 5xx/timeout, tải chào mời so với request đã gửi/hoàn tất/goodput, p95 trên mẫu thành công, clock/replay và recovery. H02 là người học xác nhận lịch/rubric; AI có thể ghi lại thông tin được cung cấp, nhưng không thay việc hiểu bài hoặc liên hệ giảng viên.

## 4. Điều phối

Theo quy trình chuẩn tại [AGENTS.md](../AGENTS.md): root điều phối và sau báo cáo cuối giao gói sẵn sàng tiếp theo theo dependency/gate; Luna mức low chỉ nhận ngữ cảnh tối thiểu, worker không tự tạo agent khác; chờ hoàn tất, không polling. Tối đa ba worker độc lập theo số vị trí chạy dự kiến thực tế. Worker thực hiện thay đổi và kiểm tra cần thiết; root xử lý xung đột cụ thể, không lặp việc đã xong. Bàn giao nội bộ bằng English, gồm ID, file/kết quả, kiểm tra/lỗi/bỏ qua, giới hạn và điều kiện tiếp theo; root trả lời user bằng Vietnamese. Với phép đo, ghi thêm revision/cấu hình/checksum.

Khi cần prompt giao việc cho agent, điền gói và phạm vi file theo mẫu:

**Prompt chỉ dành cho agent; giữ nguyên bằng tiếng Anh:**

Với đo live, worker dùng detached checkout sạch tại revision cố định; thay đổi docs/UI trong workspace chính không được làm bẩn checkout hoặc đổi revision đo. Build và lưu image inspect trước khi load. Không chạy test/build/plot nặng, cài tooling hay poll browser trong lúc đo overhead. Gắn nhãn riêng cho CLI measurement và UI integration. Lưu plan/script trong `artifacts/` hoặc `/tmp`, chỉ ghi worklog vào repo sau phép đo. Không chạy workload Docker đồng thời. Giữ metadata thực tế nguyên vẹn. Worker không commit hoặc chạm file ngoài ownership. Không lặp full checks nếu không có thay đổi mới, failure hay concern cụ thể. Archive/checksum một lần mỗi batch rồi tham chiếu manifest.

```text
Task IDs: <IDs>. Owned paths: <exact paths>.
Read docs/context/PROJECT_BRIEF.md, then <minimum task-relevant notes>; follow AGENTS.md.
Inspect relevant code before changes. Implement only the scoped requirement. Do not spawn agents,
commit, or edit outside ownership. Perform necessary focused checks. For measurements preserve
revision, config, raw artifacts, quality flags and checksums; use a new output path and retain
invalid runs. Return a concise English handoff: IDs, changed files/result paths, checks and
failures/skips, limits and next prerequisite. Include revision/config/artifact checksums for measurements.
```

## 5. Lệnh tham chiếu cho phiên sau — không chạy trong phiên lập kế hoạch

Các đường dẫn `NEW` là chỗ thay bằng output mới; runner từ chối output có sẵn. Lệnh này chỉ chạy **một normal gate lượt**, không thay vòng gate/quality/stop rule:

```bash
export GOCACHE=/tmp/project3-resume-go-cache
CUSTOM_PROFILE=normal CUSTOM_MODE=redis CUSTOM_ALGORITHM=fixed-window \
CUSTOM_INSTANCES=2 CUSTOM_RPS=20 CUSTOM_LEGIT_RPS=20 CUSTOM_DURATION=30 \
CUSTOM_LIMIT=20 CUSTOM_WINDOW_MS=1000 CUSTOM_CAPACITY=20 CUSTOM_RATE=20 \
CUSTOM_BACKEND_CAPACITY=4 CUSTOM_BACKEND_SERVICE_MS=50 CUSTOM_FAIL_POLICY=closed \
bash scripts/research-pilot.sh --case custom --repetitions 1 --analyze --output artifacts/gate-normal-NEW
python3 docs/worklog/2026-10-13-postfix/check-quality.py artifacts/gate-normal-NEW/custom-repeat-1
```

Quality checker lưu trữ chỉ dành cho normal/mixed khi Redis khỏe và ghi `quality.json` trong thư mục kết quả mới; không áp nguyên quy tắc lỗi Redis khỏe cho outage hoặc dùng checker này cho burst/concurrent. Với Mixed, đổi profile thành `mixed`, tổng RPS120/client hợp lệ20; baseline none/local/Redis đổi mode trong cùng manifest/cấu hình kiểm soát. Chính sách khác tuân theo protocol đã chọn, không tự ghi đè chỉ vì lệnh ví dụ.

```bash
# Kiểm tra code khi có thay đổi; Redis integration cần instance test riêng:
bash scripts/verify.sh
REDIS_TEST_ADDR=127.0.0.1:TEST_PORT go test -race ./internal/limiter -count=1
# Export sau freeze, dùng manifest thật, output mới:
python3 scripts/report-study.py path/to/locked-manifest.json --output artifacts/report-NEW
# Mở demo sau khi restore saved folders; không tự bắt đầu benchmark:
go run ./cmd/console
```

`TEST_PORT` phải thay bằng port instance test do phiên sở hữu; không chạy test lên Redis đang đo, không `FLUSHDB`, prune hoặc xóa project khác. Quyền Docker/loopback có thể cần sandbox escalation; không suy permission denied là test logic failed. Khi code không đổi, ưu tiên chỉ kiểm chứng môi trường/gói đang làm thay vì chạy suite lại.

## 6. Commit, checkpoint và điều kiện dừng

Mỗi commit chỉ chứa một feature hoặc một fix cùng tests trực tiếp liên quan; không gộp nhiều thay đổi độc lập. Evidence calibration, protocol, dataset, analysis và checkpoint tiến độ có commit riêng. Đây là yêu cầu commit được người dùng làm rõ trong phiên 19/10. Code thay đổi sau protocol phải được ghi revision/version và pilot lại phần ảnh hưởng. Mã và kết quả không được trộn ngầm giữa revisions.

Checkpoint cuối phiên chỉ cần cập nhật: ID đã xong/còn chờ, gate/điều kiện chặn tiếp theo, commit/revision, kết quả/manifest, kiểm tra đã chạy, phạm vi/checkout/process còn lại, lệnh tiếp theo và quyết định cần người học/giảng viên. Brief có liên kết tới checkpoint; không chép toàn bộ hội thoại vào docs hoặc lặp lại cùng worklog nhiều lần.

Khi người dùng yêu cầu dừng hoặc hạn chế lượt làm việc: không giao việc mới, dừng tiến trình do phiên sở hữu và dọn đúng project, giữ lại artifacts chưa hoàn chỉnh, commit phần đã kiểm chứng hoặc ghi rõ phần chưa kiểm chứng. Không xóa file có sẵn để làm trạng thái đẹp hơn. Chỉ dọn worktree phụ sau khi lưu bằng chứng; chỉ push khi được yêu cầu.

**Trạng thái hiện tại:** T09 đã thu thập đủ dữ liệu: 138/138 vị trí chạy dự kiến dùng được và 46/46 cấu hình được tổng hợp. Archive/checksum bằng chứng cuối và việc dọn dẹp đã được xác minh. Không chạy thêm tải; dừng trước T10. T10 chưa bắt đầu và chưa có kết luận RQ. Bằng chứng T04–T08 có giới hạn; không chạy lại nếu chưa có finding liên quan. Các mục todo mô tả phạm vi đã biết, không phải cam kết thời gian/chi phí hay rubric chưa được cung cấp.
