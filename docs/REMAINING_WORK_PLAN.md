# Công việc còn lại và kế hoạch tiếp tục Project 3

**Kế hoạch gốc 13/10/2026; cập nhật trạng thái 19/10/2026.** Người dùng đã cho phép tiếp tục phần kỹ thuật/tài liệu, bắt đầu T01–T02; việc học do người dùng thực hiện với GPT. Các dependency/quality gate vẫn giữ nguyên, chưa chạy benchmark chính thức. Đây là danh sách công việc còn lại theo phạm vi hiện biết, gồm nghiên cứu, code phục vụ phép đo, tài liệu, demo và việc người học cần làm. Ngày nộp/bảo vệ, rubric và phản hồi tiếp theo của giảng viên chưa xác định đầy đủ, nên có thể phát sinh điều chỉnh. Không dùng số lượng checkbox để suy phần trăm hoàn thành.

Nguồn yêu cầu: [Roadmap](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md). Các tham số, ma trận và cách điều phối dưới đây là lựa chọn kỹ thuật/đề xuất, chưa phải protocol đã khóa hoặc yêu cầu được giảng viên duyệt. [Checkpoint](context/SESSION_CHECKPOINT.md) ghi phần đã xong; [readiness](experiments/PROTOCOL_READINESS.md) ghi điều kiện chưa đạt.

**Kết quả tiếp tục ngày 19/10:** T01 vẫn chưa đạt (ba bước nhảy realtime khoảng 2,93–2,96 giây trong 90 giây); không chạy T03. T02 đã chuẩn bị helper portable và qua bốn self-check, chưa kiểm chứng live gate. T11 có [bản nháp báo cáo](REPORT_DRAFT.md); T12 đã chuẩn bị saved-run demo, chưa phải bộ nộp cuối. Xem [checkpoint](context/SESSION_CHECKPOINT.md) cho evidence, checks và điều kiện tiếp theo.

## 1. Những phần đã xong, không cần làm lại

- Prototype Go/API/backend/LB, local và Redis Lua cho FW/TB, topology 1/2/4, generator và analyzer đã có.
- Lỗi float local TB và deadline Redis đã có sửa/test/evidence; không cần điều tra lại từ đầu nếu không có finding mới.
- Console chọn lượt, hiển thị chất lượng và so sánh runtime content đã kiểm tra trên Docker thật và desktop/mobile.
- Đã có archive/checksum, exporter CSV/Markdown, hình pilot và kịch bản demo. Kiểm tra cuối đã đạt; không chạy lại toàn suite chỉ để bắt đầu phiên.
- Bối cảnh doanh nghiệp flash sale giả định đã chọn. Không mở lại lựa chọn stack/kiến trúc hoặc biến đồ án thành gateway/HA.

**Nút chặn:** realtime host nhảy khoảng 2,6 giây trên WSL2, observer độc lập xác nhận. Chưa biết tác nhân điều chỉnh clock. Socket mitigation không sửa được clock host. Gate hai lượt normal 30 giây bị dừng dù request thành công đầy đủ. Chưa có benchmark chính thức hoặc kết luận cuối RQ1–RQ5.

## 2. Toàn bộ todo theo thứ tự phụ thuộc

| ID | Công việc còn lại | Phụ thuộc | Đầu ra / điều kiện hoàn thành |
| --- | --- | --- | --- |
| T01 | Xác định môi trường có clock ổn định; chẩn đoán read-only hoặc chuyển máy/môi trường đo | Không | Observer mới và thông tin môi trường; không còn step trong cửa sổ quan sát, tiếp tục kiểm tra mọi run. Không tự đổi clock/NTP/clocksource khi chưa xác định tác nhân/phạm vi được phép. |
| T02 | Chuẩn bị observer/gate tái chạy được, không phụ thuộc `/tmp` phiên cũ | Không, có thể chuẩn bị trước T01 | Output mới, timeout hữu hạn, quality checks và stop rule; chỉ sửa helper nhỏ cần thiết, không thêm framework. |
| T03 | Chạy lại gate normal/mixed sau sửa, kiểm chứng generator/clock/healthy Redis | T01–T02 | Theo PRESET: normal Redis FW rồi mixed Redis FW, tối đa 3 lượt mỗi nhóm × 30 giây; mọi lượt/quality flags được giữ; dừng khi cùng blocker xuất hiện hai lượt. |
| T04 | Hiệu chỉnh phép so normal/burst FW/TB × local/Redis và baseline none | T03 | Cùng policy rate, workload/key/backend/topology; xác minh burst phase, sample count và clock; không gọi B=Q,r=Q/W là burst semantics tương đương. |
| T05 | Hiệu chỉnh scaling 1/2/4 với tải dưới/gần/trên ngưỡng | T03 | Sweep có quota headroom và generator đạt tải; ghi bottleneck API/LB/Redis/backend/host. Không coi tăng reject trên một key là tăng accepted throughput. |
| T06 | Chốt bằng chứng concurrent/atomicity cho RQ4, gồm quota gần cạn | T03 | Chọn tests/invariants + non-atomic control hiện có hoặc harness bổ sung tối thiểu; mô tả concurrency thực và giới hạn. Không tự xây non-atomic HTTP service. |
| T07 | Hoàn thiện schema/lifecycle runner outage và hiệu chỉnh recovery | T03 | Có baseline Redis khỏe, open/closed, timestamps bốn sự kiện, policy/config/metrics đủ, thời gian post-outage đủ; chọn threshold trước đo. |
| T08 | Khóa protocol và manifest phiên bản cụ thể | T04–T07 | Mọi biến, số lượt/thời lượng, thứ tự, reset/warm-up, fidelity/exclusion/retry/recovery và ánh xạ RQ được ghi trước bộ chính thức. |
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

### T04–T07: calibration còn thiếu và code chỉ khi cần

T04/T05 tái dùng `research-pilot.sh --case custom`: topology1/2/4, duration3–30s, repetitions1–3, RPS≤1000 và 5 legitimate keys. Nếu giới hạn quota/key/backend chặn phép đo scaling, ghi lại và thiết kế workload headroom trước; không mở tải/config tùy ý chỉ để benchmark trông mạnh hơn. Burst sát biên FW chưa được runner đồng bộ server window; chỉ bổ sung nếu kết luận cần thí nghiệm đó.

T06: tests Redis thật có Lua atomic và non-atomic control; batch HTTP hiện chưa có phase preconsume quota. Chốt trước liệu test gần cạn là bằng chứng đủ hay cần harness tối thiểu. Control có barrier chỉ chứng minh tình huống race được tạo, không suy tần suất race tự nhiên hoặc so performance HTTP từ test.

T07: [redis-outage.sh](../scripts/redis-outage.sh) dùng helper cũ, workload10s/pause2s, Compose YAML và chủ yếu backend-before/API-after. Chưa tự tạo đầy đủ `policy.json`, resolved JSON, before/after mọi API, revision/images/inspect theo schema analyzer/exporter mới. Công việc là đồng nhất case artifacts, output mới không ghi đè, lifecycle/timeout/cleanup hữu hạn và namespace/state rõ, tái dùng sampling/analyzer hiện có. Không coi gọi thêm `--analyze` lên output thiếu policy là hoàn thành.

Outage cần healthy baseline cùng tải/backend/topology/policy; ghi pause/unpause requested/completed, tách transition; chọn thời lượng đủ full post windows. Recovery candidate window1s,min5 legitimate samples,3 consecutive windows và threshold từ healthy calibration được ghi trước đo. TB outage chỉ thêm nếu cần kết luận riêng về TB. Không biến pause Redis thành nghiên cứu HA/restart/data loss. Quota khi thiếu response/state chỉ báo lower bound/unknown, không suy absolute pass.

Nếu drops tái diễn trên clock ổn: dùng đối chứng sampler bật/tắt cùng tải trước khi sửa scheduler. Không xóa nhánh bỏ stale schedules, tăng timeout hoặc giảm tải chỉ để xóa flags. Network overhead có trong Proposal: kiểm tra khả năng lấy Redis network-counter deltas/đơn vị/sampling đáng tin trước protocol; chỉ báo nếu đủ evidence, không thay latency difference bằng khẳng định bytes/request.

### T08–T10: protocol, thực chạy và đánh giá

Dùng [PROTOCOL_CANDIDATE](experiments/PROTOCOL_CANDIDATE.md), [ANALYSIS](experiments/ANALYSIS.md) và [REPORTING](experiments/REPORTING.md). Tài liệu candidate có những status lịch sử đã cũ: checkpoint/readiness/worklogs mới xác nhận đã sửa và có pilot HTTP. Không đọc câu cũ “chưa pilot” thành công việc phải làm lại toàn bộ.

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

Commit theo gói: helper/harness + test; calibration evidence; protocol khóa; raw dataset + manifests; analysis/figures; report/slides/demo final. Code thay đổi sau protocol phải được ghi revision/version và pilot lại phần ảnh hưởng. Mã và kết quả không được trộn ngầm giữa revisions.

Checkpoint cuối phiên chỉ cần cập nhật: IDs done/pending, next gate/blocker, commit/revision, output/manifests, tests đã chạy, ownership/checkout/process còn lại, lệnh tiếp theo và quyết định cần người học/giảng viên. Brief có link tới checkpoint; không copy toàn chat vào docs hoặc ghi lại cùng worklog nhiều lần.

Người dùng yêu cầu dừng/quota ít: ngừng phát việc mới, dừng process do phiên sở hữu và cleanup đúng project, giữ partial artifacts, commit phần đã kiểm chứng hoặc ghi rõ phần chưa kiểm chứng. Không xóa file có sẵn để làm status đẹp. Worktree phụ chỉ dọn sau khi evidence đã lưu; push chỉ khi được yêu cầu.

**Điểm bắt đầu khi được yêu cầu tiếp tục:** T01 xác định môi trường clock và T02 chuẩn bị portability; T03 chỉ sau cả hai. Không tự chạy T09 hoặc tinh chỉnh UI mở rộng khi T01–T08 chưa đạt. Toàn bộ todo ở bảng là phạm vi hiện biết, không cam kết thời lượng/chi phí token hoặc rubric chưa được cung cấp.
