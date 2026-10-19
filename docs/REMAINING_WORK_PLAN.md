# Công việc còn lại và kế hoạch tiếp tục Project 3

**Kế hoạch gốc 13/10/2026; cập nhật trạng thái 19/10/2026.** T01 current-session stability, T02/T03 pilot gate, T04 normal/burst calibration, T05 scaling calibration và T06 atomicity evidence đã hoàn tất trong giới hạn đã ghi; T07 bounded recovery calibration và exporter smoke cũng đã hoàn tất; phiên dừng trước T08; phần học do người dùng thực hiện với GPT. Các dependency và quality gate được giữ nguyên; chưa chạy benchmark chính thức. Đây là danh sách phần việc còn lại đã biết về nghiên cứu, code đo lường, tài liệu, demo và việc người học cần làm. Người dùng chọn mốc nộp tạm **giữa tháng 12/2026** ngày 19/10; ngày nộp/bảo vệ chính thức, rubric và phản hồi tiếp theo của giảng viên chưa xác định đầy đủ, nên có thể phát sinh điều chỉnh. Không dùng số lượng checkbox để suy phần trăm hoàn thành.

Nguồn yêu cầu: [Roadmap](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md). Các tham số, ma trận và cách điều phối dưới đây là lựa chọn kỹ thuật/đề xuất, chưa phải protocol đã khóa hoặc yêu cầu được giảng viên duyệt. [Checkpoint](context/SESSION_CHECKPOINT.md) ghi phần đã xong; [readiness](experiments/PROTOCOL_READINESS.md) ghi điều kiện chưa đạt.

**Phiên đã hoàn tất T07 và dừng trước T08:** T04 có 10 lượt normal/burst đạt quality; T05 có 27 cells hợp lệ, giữ riêng một lượt drop và ba lượt gián đoạn; T06 có tests Redis thật. T07 có bốn capacity10 healthy/outage cases trên checkout sạch, zero drops, hai healthy gates đạt, recovery ổn định 4s theo tiêu chí cửa sổ và exporter smoke 4/4 usable. [Evidence T07](worklog/2026-10-19-outage-recovery/README.md) giữ riêng dữ liệu đo `09b1249` và exporter fix `5e5282b`; batch capacity4 sơ bộ vẫn nguyên vẹn. T08 chỉ là draft chưa khóa, network mới test offline. Chờ người dùng tiếp tục trước thí nghiệm tiếp theo.

**Cập nhật gate 19/10:** T01 clock stability trong phiên hiện tại đã đạt; độ chính xác UTC tuyệt đối và độ bền sau restart/resume chưa xác minh. T02 observer/runner/checker lifecycle đã chạy live; T03 hoàn tất sáu lượt normal/mixed có giới hạn, không có quality flag hay generator drop. Oracle Fixed Window chưa kết luận được vì các window chỉ quan sát một phần; protocol và benchmark chính thức chưa khóa/chưa chạy. T11 có [bản nháp báo cáo](REPORT_DRAFT.md); T12 có chuẩn bị saved-run demo, chưa phải bộ nộp cuối. Xem [T01 worklog](worklog/2026-10-19-clock-remediation/README.md), [T02/T03 gate worklog](worklog/2026-10-19-measurement-gate/README.md) và [checkpoint](context/SESSION_CHECKPOINT.md).

## 1. Những phần đã xong, không cần làm lại

- Prototype Go/API/backend/LB, local và Redis Lua cho FW/TB, topology 1/2/4, generator và analyzer đã có.
- Lỗi float local TB và deadline Redis đã có sửa/test/evidence; không cần điều tra lại từ đầu nếu không có finding mới.
- Console chọn lượt, hiển thị chất lượng và so sánh runtime content đã kiểm tra trên Docker thật và desktop/mobile.
- Đã có archive/checksum, exporter CSV/Markdown, hình pilot và kịch bản demo. Kiểm tra cuối đã đạt; không chạy lại toàn suite chỉ để bắt đầu phiên.
- Bối cảnh doanh nghiệp flash sale giả định đã chọn. Không mở lại lựa chọn stack/kiến trúc hoặc biến đồ án thành gateway/HA.

**Trạng thái gate:** các bước nhảy realtime WSL trước đây được giữ làm bằng chứng lịch sử. Observer T02 mới và cả sáu quality check ở từng lượt T03 đều đạt trong phiên hiện tại. Độ chính xác UTC tuyệt đối và độ bền sau resume/restart vẫn chưa xác minh; còn network live validation và khóa T08 trước phép đo chính thức hoặc kết luận RQ1–RQ5.

## 2. Toàn bộ todo theo thứ tự phụ thuộc

| ID | Công việc còn lại | Phụ thuộc | Đầu ra / điều kiện hoàn thành |
| --- | --- | --- | --- |
| T01 | Xác định môi trường có clock ổn định; chẩn đoán read-only hoặc chuyển máy/môi trường đo | Không | **Đạt ổn định trong phiên hiện tại:** observer 90 giây sau remediation không ghi nhận step >5 ms. Độ chính xác UTC tuyệt đối (Windows lệch khoảng 4,05 giây) và độ bền sau restart/resume chưa xác minh. Live gate T02/T03 hoàn tất như [worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T02 | Chuẩn bị observer/gate tái chạy được, không phụ thuộc `/tmp` phiên cũ | Không, có thể chuẩn bị trước T01 | **Hoàn tất:** observer 90 giây mới và live runner/checker lifecycle tại revision cố định; raw output/checksum trong [T02/T03 worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T03 | Chạy lại gate normal/mixed sau sửa, kiểm chứng generator/clock/healthy Redis | T01–T02 | **Hoàn tất pilot gate:** 3 normal + 3 mixed × 30 giây đạt mọi quality check, không có drop. Oracle FW `inconclusive`; đây không phải correctness pass hoặc benchmark chính thức. |
| T04 | Hiệu chỉnh phép so normal/burst FW/TB × local/Redis và baseline none | T03 | **Hoàn tất calibration có giới hạn:** 10 cells × 1 lượt × 30 giây, 10.800 sent=scheduled, không drop/quality flag; cùng policy rate, workload/key/backend/topology, đã kiểm tra từng pha/class. Xem [T04 worklog](worklog/2026-10-19-calibration-next/README.md). FW inconclusive, một lượt không đủ kết luận so sánh hiệu năng; B=Q,r=Q/W không đồng nhất burst semantics. |
| T05 | Hiệu chỉnh scaling 1/2/4 với tải dưới/gần/trên ngưỡng | T03 | **Hoàn tất calibration có giới hạn:** 27 cells hợp lệ × 10 giây, 43.200 sent, không drop/quality flag trong các lượt hợp lệ; quota headroom, một replacement cùng cấu hình, giữ một lượt drop và ba lượt gián đoạn. Backend chung giới hạn khoảng 190 success/s ở 250 RPS; chưa chứng minh API scaling hoặc mode tốt hơn. [T05 worklog](worklog/2026-10-19-calibration-next/T05-README.md). |
| T06 | Chốt bằng chứng concurrent/atomicity cho RQ4, gồm quota gần cạn | T03 | **Hoàn tất bằng chứng test có giới hạn:** shared quota và quota gần cạn FW/TB đạt trên Redis thật, kèm đối chứng non-atomic ép race; xem [T06 worklog](worklog/2026-10-19-atomicity/README.md). Không suy tần suất race tự nhiên hoặc hiệu năng HTTP từ test. |
| T07 | Hoàn thiện schema/lifecycle runner outage và hiệu chỉnh recovery | T03 | **Hoàn tất bounded calibration:** 4 cases × 30s, 12.000 sent=scheduled, zero drops, healthy gates đạt; stable recovery 4s theo 1s/min5/3 windows, first success riêng. Exporter smoke 4/4 usable sau fix null resources riêng; FW vẫn inconclusive. [T07 recovery](worklog/2026-10-19-outage-recovery/README.md). |
| T08 | Khóa protocol và manifest phiên bản cụ thể | T04–T07 | **Chưa khóa:** có draft cells nhưng planned runs/order/revision/threshold chưa hoàn chỉnh; network counters mới qua 20 tests offline, còn live validation. Mọi biến và rule phải khóa trước bộ chính thức. |
| T09 | Chạy benchmark chính thức tuần tự và khóa dữ liệu | T08 | Đủ cells/lượt theo manifest; raw/config/counters/runtime content/revision/checksum; invalid vẫn lưu, replacement có lý do theo rule đã khóa. |
| T10 | Phân tích và xuất bảng/hình trả lời RQ1–RQ5 | T09 | Hình truy về run/cell/revision; biến thiên giữa lượt, attribution lỗi, oracle/giới hạn rõ; không gộp percentile sai hoặc chọn kết quả đẹp. |
| T11 | Hoàn thiện báo cáo và sửa theo phản hồi giảng viên | Khung có thể viết ngay; kết quả đợi T10 | Bối cảnh → pain point → tác động → yêu cầu → giải pháp → thí nghiệm → đánh giá → phát triển tương lai; không quy mô phỏng thành doanh thu thật. |
| T12 | Đóng gói demo/source, restore saved runs và thử clean checkout | Có thể chuẩn bị ngay; bản cuối đợi T09–T10 | Lệnh chạy/reproduce, saved UI và offline fallback; không overwrite artifacts; report/slide/demo cùng phiên bản bộ nộp cuối. |
| T13 | Hoàn thiện slide, diễn tập và bộ nộp | T10–T12 | Slide/demo có thời lượng, hỏi đáp, phương án mất Docker/internet, định dạng/hạn nộp đúng; commit/tag cuối và worktree sạch. |
| H01 | Tự kiểm tra kiến thức nền/thuật toán/phương pháp đo | Song song mọi giai đoạn | Người học tự giải thích/tính tay; AI không tự đánh dấu đã hiểu. Dùng câu hỏi trong PROJECT_ROADMAP và DEMO_SCRIPT. |
| H02 | Xác nhận ngày nộp/bảo vệ, rubric và yêu cầu hình thức với giảng viên | Song song; cần người học | Cập nhật kế hoạch khi có thông tin, không tự gửi email/tin nhắn hoặc suy rubric từ tài liệu dự án. |

Sliding Window, dashboard lớn, auth/RBAC, Redis Cluster, Kubernetes, gateway, thêm framework frontend là **tùy chọn/out of scope**, không thuộc todo cần hoàn tất baseline. Lỗi mới ảnh hưởng validity/correctness là công việc điều kiện, không là lý do tự mở rộng tính năng.

## 3. Cách triển khai các phần kỹ thuật còn mở

### T01–T03: clock và gate

Tái dùng [observer](worklog/2026-10-13-clock/observe.py), [PRESET](worklog/2026-10-13-postfix/PRESET.md) và [quality checker](worklog/2026-10-13-postfix/check-quality.py). Observer archival có đường dẫn `/tmp/project3-clock-observer` cố định; [run-gate](worklog/2026-10-13-postfix/run-gate.sh) còn gọi `/tmp/postfix-quality.py` và output cũ. Chúng là evidence cách chạy trước đây, **không chạy nguyên bản như portable runner**. Phiên tiếp theo sửa bản helper tối thiểu để lấy checker từ repo và dùng output mới; helper mới/sửa có self-check hoặc focused test, không thay raw archival.

Gate chạy từng lượt (`--repetitions 1`), kiểm tra quality rồi mới chạy lượt sau; đếm blocker xuyên các lượt. Một lệnh `--repetitions 3` hiện không tự đánh giá quality giữa lượt để dừng sớm. Candidate gate giữ Q=B=20,W=1000ms,r=20/s; 2 API,5 legitimate keys, backend capacity4/service50ms; normal20 RPS, mixed120/20; request/dial/pool100ms, generator2s/inflight200; 1s sau health không có tải warm-up.

Điều kiện đã đặt: 0 drops, raw/summary/counters reconcile, không healthy Redis errors, offered rate từng pha/class ±5%, p95 lag ≤10ms và ≤send interval; wall–monotonic residual cả scheduling và response latency ≤5ms. Normal không reject/overload. Overload chủ ý trong mixed và fallback chủ ý trong outage là outcome. FW partial-window `inconclusive` không tự làm lượt invalid, nhưng không là correctness pass. Không tăng ngưỡng clock hoặc sửa timestamp để che step.

### T04–T07: calibration và bằng chứng đã hoàn tất

**T04/T05 đã hoàn tất calibration, T06 đã chốt bằng chứng tests:** không chạy lại nếu không có finding/đổi code liên quan. T04/T05 đã tái dùng `research-pilot.sh --case custom`: topology1/2/4, duration3–30s, repetitions1–3, RPS≤1000 và 5 legitimate keys. Nếu giới hạn quota/key/backend chặn phép đo scaling, ghi lại và thiết kế workload headroom trước; không mở tải/config tùy ý chỉ để benchmark trông mạnh hơn. Burst sát biên FW chưa được runner đồng bộ server window; chỉ bổ sung nếu kết luận cần thí nghiệm đó.

T06: tests Redis thật có Lua atomic và non-atomic control; batch HTTP hiện chưa có phase preconsume quota. Đã chọn bằng chứng invariants + tests quota gần cạn FW/TB, không thêm non-atomic HTTP service. Control có barrier chỉ chứng minh tình huống race được tạo, không suy tần suất race tự nhiên hoặc so performance HTTP từ test.

T07: [redis-outage.sh](../scripts/redis-outage.sh) đã có policy/resolved JSON, counters trước/sau mọi API/backend, revision/images/inspect, unique IDs, parent metadata và analysis cho cả healthy/outage. Startup/cleanup hữu hạn và healthy gate có 4 mocks. Live capacity10/50ms, 100/20 RPS, 30s, pause4s/2s đã hoàn tất trên checkout sạch; recovery ổn định 4s theo tiêu chí cửa sổ, exporter smoke 4 cases usable. Null-resource exporter fix có 7 regression tests. Batch capacity4 overload/dirty status vẫn là evidence lịch sử, không sửa metadata cũ. Xem [worklog](worklog/2026-10-19-outage-recovery/README.md); không chạy lại khi chưa có finding mới.

Outage cần healthy baseline cùng tải/backend/topology/policy; ghi pause/unpause requested/completed, tách transition; chọn thời lượng đủ full post windows. Recovery candidate window1s,min5 legitimate samples,3 consecutive windows và threshold từ healthy calibration được ghi trước đo. TB outage chỉ thêm nếu cần kết luận riêng về TB. Không biến pause Redis thành nghiên cứu HA/restart/data loss. Quota khi thiếu response/state chỉ báo lower bound/unknown, không suy absolute pass.

Nếu drops tái diễn trên clock ổn: dùng đối chứng sampler bật/tắt cùng tải trước khi sửa scheduler. Không xóa nhánh bỏ stale schedules, tăng timeout hoặc giảm tải chỉ để xóa flags. Network overhead có trong Proposal: kiểm tra khả năng lấy Redis network-counter deltas/đơn vị/sampling đáng tin trước protocol; chỉ báo nếu đủ evidence, không thay latency difference bằng khẳng định bytes/request.

### T08–T10: protocol, thực chạy và đánh giá

Dùng [PROTOCOL_CANDIDATE](experiments/PROTOCOL_CANDIDATE.md), [ANALYSIS](experiments/ANALYSIS.md) và [REPORTING](experiments/REPORTING.md). Candidate đã có bản nháp cells; planned runs/order/source revision/threshold còn mở, chưa phải protocol khóa. Network sampling mới có offline checks; phải live-validate sau khi được tiếp tục. Checkpoint/readiness/worklogs là nguồn trạng thái hiện tại; không làm lại các pilot đã hoàn tất nếu không có finding mới.

Manifest khóa liệt kê tường minh cell/RQ/repetition/config; deduplicate baseline dùng chung, không nhân toàn ma trận84. Chốt trước cold-start hoặc warm-up, sample đủ cho tail percentiles, run order, resource budget/host metadata, fidelity, clock, invalid/retry và recovery. `3×30s` là candidate, không phải mặc định nghiên cứu đã duyệt. Mọi thay đổi protocol sau đó có version và lý do; dữ liệu cũ không ghép ngầm với version mới.

Exporter hiện kiểm tra consistency **trong cell**, không tự chứng minh hai cell là phép so có kiểm soát. Người phân tích phải đối chiếu biến giữ cố định, workload/key/algorithm/state/topology/backend/revision/runtime content. Report median/min–max của metrics từng lượt, giữ mọi invalid, không gọi median p95 là p95 gộp. Lua/race, legitimate goodput/tail, backend outcomes, Redis CPU cores/memory/network nếu có, outage availability/recovery phải có evidence tương ứng; không mặc định exporter hiện đã xuất mọi figure/metric cuối.

`plot-calibration.py` hiện chỉ vẽ mixed pilot từ schema calibration JSON, không phải plotting pipeline cuối cho mọi RQ. T10 tạo các hình thuật toán/scaling/atomicity/outage từ dữ liệu đo thật bằng công cụ plotting chuẩn; Matplotlib là tooling offline, không dependency Go/runtime. Bộ hình/bảng cuối có manifest/source/caption, giới hạn và phiên bản; không dùng hình pilot như số liệu chính thức.

### T11–T13 và H01–H02: sản phẩm để nộp

Khung báo cáo và phần nền có thể viết khi clock chưa ổn. Chương kết quả, kết luận và slide kết quả đợi T10. Cần tài liệu liên quan/tài liệu tham khảo phù hợp, lý do policy/time/atomicity/fail policy, mô tả máy đo/threats to validity, phản hồi giảng viên và định dạng theo rubric khi có; không tạo nguồn trích dẫn hoặc số liệu giả.

Đóng gói demo theo [DEMO_SCRIPT](DEMO_SCRIPT.md). Saved runs final nằm trong archive [Console content](worklog/2026-10-13-console-content/README.md), folder có prefix mode; controller chỉ nạp `artifacts/console/<status.id>/status.json`. Restore toàn folder theo ID gốc vào thư mục chưa tồn tại, không sửa metadata/checksum. Local run có clock flag phải giữ. Hình hiện tại lấy calibration cũ, không ghép số liệu/revision với final Console triplet. Bản nộp cuối dùng một version code/protocol/dataset thống nhất, demo offline fallback và lệnh reproduce đã thử trên checkout sạch.

H01 gồm tính tay FW/TB/burst/refill, quota local N instances, Lua atomic/race,429 vs5xx/timeout, offered vs sent/completed/goodput, p95 mẫu thành công, clock/replay và recovery. H02 là việc người học xác nhận lịch/rubric; AI có thể ghi lại thông tin được cung cấp, không thay việc hiểu hoặc liên hệ giảng viên.

## 4. Điều phối

Theo workflow chuẩn tại [AGENTS.md](../AGENTS.md): root điều phối và sau báo cáo cuối phân công gói sẵn sàng tiếp theo theo dependency/gate; Luna low nhận context tối thiểu, worker không tự spawn; chờ completion, không polling. Tối đa ba workers độc lập theo slot thực tế. Worker làm implementation và checks; root xử lý conflict cụ thể, không lặp việc đã xong. Handoff nội bộ bằng English, gồm IDs, files/results, checks/failures/skips, limits/next prerequisite; root trả lời user bằng Vietnamese. Measurement thêm revision/config/checksum.

Khi cần agent-facing prompt, điền gói và ownership theo mẫu:

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

Quality checker archival chỉ dành normal/mixed healthy, ghi `quality.json` trong output mới; không áp nguyên rule healthy-errors cho outage hoặc dùng nó làm checker burst/concurrent. Mixed đổi profile thành `mixed`, tổng RPS120/legitimate20; baseline none/local/Redis thay mode trong cùng manifest/control settings. Chính sách khác đi theo protocol đã chọn, không tự override chỉ vì lệnh ví dụ.

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

Checkpoint cuối phiên chỉ cần cập nhật: IDs done/pending, next gate/blocker, commit/revision, output/manifests, tests đã chạy, ownership/checkout/process còn lại, lệnh tiếp theo và quyết định cần người học/giảng viên. Brief có link tới checkpoint; không copy toàn chat vào docs hoặc ghi lại cùng worklog nhiều lần.

Người dùng yêu cầu dừng/quota ít: ngừng phát việc mới, dừng process do phiên sở hữu và cleanup đúng project, giữ partial artifacts, commit phần đã kiểm chứng hoặc ghi rõ phần chưa kiểm chứng. Không xóa file có sẵn để làm status đẹp. Worktree phụ chỉ dọn sau khi evidence đã lưu; push chỉ khi được yêu cầu.

**Điểm bắt đầu khi được yêu cầu tiếp tục:** T08 prerequisites: network sampler live validation, hoàn thiện manifest/run order/revision và khóa các rule trước benchmark. T04–T07 đã đạt đầu ra calibration/test có giới hạn; không tự chạy lại. Kiểm tra clock trước tải nếu restart/resume hoặc không rõ tính liên tục. Chưa chạy T09 khi T08 chưa khóa. Phiên dừng sau T07 nên không dispatch gói tiếp theo. Toàn bộ todo ở bảng là phạm vi hiện biết, không cam kết thời lượng/chi phí token hoặc rubric chưa được cung cấp.
