# Điều tra Redis timeout và generator drops — 13/10/2026

Điều tra read-only archive pilot revision `018a0a2facc9fa56d3defa074c74bd01bc42e74a`; không chạy Docker/tải, không sửa runtime. Theo Roadmap, phải tách fallback/lỗi dịch vụ khỏi quota reject và xác nhận offered load trước so sánh chính thức. Đây là chẩn đoán kỹ thuật, chưa phải kết quả nghiên cứu khóa protocol.

Archive gốc: [console-matrix-artifacts.tar.gz](../2026-10-12-console-matrix/evidence/console-matrix-artifacts.tar.gz). SHA256 `60aed17a9ea0688b425abe82bab3179ff841d558b27dd3f8ae0e7b8902f19b9d`, khớp manifest; xác nhận đủ 1.148 input checksum. Giải nén riêng tại `/tmp/project3-redis-drops`; không ghi lại analyzer hay input. Bảng dưới lấy trace JSONL, **mọi** API before/after, compose logs/config và metadata trong từng `artifacts/console/<ID>/result/custom-repeat-1/`.

## Các lượt bị ảnh hưởng

| Lượt / Run ID | Cấu hình | Limiter errors theo instance | Drop | Bước lệch wall clock so với monotonic tại request đầu lỗi |
| --- | --- | --- | --- | --- |
| 13 / `20261012T024935-2da51a560b8f` | normal, Redis FW open, 1 API | API1: 4 open | 0 | +989,611ms, request 014 |
| 21 / `20261012T025237-feadf77b2223` | normal, Redis TB open, 4 API | API1:1, API2:0, API3:2, API4:1 open | 0 | +965,320ms, request 002 |
| 37 / `20261012T025858-6853bc633190` | mixed, Redis TB closed, 1 API | API1: 6 closed | 0 | +862,240ms, request 309 |
| 50 / `20261012T030416-aaddcf847739` | burst, local TB closed, 2 API | 0 | 4 backlog | không thấy bước lệch |
| 58 / `20261012T030750-d085475c65a7` | burst, Redis TB closed, 1 API | API1: 1 closed | 1 backlog | +880,838ms, request 178 |
| 62 / `20261012T030931-7f3f50cee463` | burst, Redis TB open, 2 API | API1:2, API2:2 open | 0 | +1.071,478ms, request 031 |

FW = Fixed Window; TB = Token Bucket. Tổng 19 errors = 12 open + 7 closed, khớp logs và decision trace. Open đều HTTP 200 và tới backend; closed đều HTTP 503 không tới backend. Generator không có transport timeout. Logs có 6 `write tcp ... i/o timeout` và 13 `i/o timeout` không chỉ rõ thao tác; không được gọi cả 19 là read timeout.

## Redis: bằng chứng mạnh hơn giả thuyết quá tải

Cả năm lượt có lỗi đều có bước nhảy wall clock ngay request đầu fallback. Tính độ lệch bằng `(sent_at - scheduled_at) theo timestamp JSON - schedule_lag_ms`. Generator tính lag bằng `time.Time.Sub` trong Go trước khi serialize nên dùng monotonic; JSON không giữ monotonic. Lệch trước bước nhảy gần 0, sau đó ổn định quanh giá trị trong bảng. `end_at - sent_at` so với `latency_ms` cũng lệch khi response vắt qua bước nhảy. Sai số làm tròn dưới khoảng 0,001ms. Không được diễn giải lệch này thành generator trễ gần một giây.

Thời gian từ `sent_at` tới `decision_at` của 19 fallback chỉ **0,825–3,510ms**, fail-closed HTTP latency **1,707–3,768ms**; open HTTP latency **52,120–57,029ms** gồm backend service 50ms. Điều này không phù hợp giải thích đơn giản rằng từng thao tác đã chờ hết 100ms vì Redis chậm.

Cấu hình archived mọi API: `REDIS_TIMEOUT=100ms`. `cmd/server/main.go` ở revision gốc đặt Dial/Read/Write/PoolTimeout cùng giá trị, `MaxRetries=-1`, `ContextTimeoutEnabled=true`; handler tạo context 100ms. Redis Lua gọi qua `redis.Script.Run`. Dependency khóa `go-redis/v9 v9.17.0`: mã dependency cài local `internal/pool/conn.go:892` lấy cache UnixNano, dựng `time.Unix(0, nowNs)` rồi cộng timeout; `global_time_cache.go` cập nhật mỗi 50ms. Deadline này mất monotonic và có thể nằm trong quá khứ ngay khi wall clock nhảy tiến vượt 100ms trước lần cache refresh. Cụm lỗi nhiều request kéo dài khoảng 26–43ms, phù hợp nhịp cache 50ms.

**Đã chứng minh:** timestamp wall/monotonic không nhất quán, trùng request đầu fallback ở mọi lượt lỗi; fallback nhanh, counters và logs khớp. **Nguyên nhân có bằng chứng mạnh:** deadline dựa trên wall-clock cache của dependency kết hợp bước nhảy đồng hồ, thay vì Redis thực xử lý chậm 100ms. **Chưa chứng minh nhân quả trực tiếp:** không có snapshot cache/deadline bên trong API tại sự kiện; trace chỉ đo clock của generator. Không xác định được ai điều chỉnh clock (host/VM/OS sync), không có packet capture, host CPU/scheduler hay Redis latency log. Không kết luận Redis bão hòa, pool cạn hoặc Docker sampling gây lỗi.

Quét cả 84 lượt thấy thêm lượt 78 (`20261012T031552-7f18ae5fc4e0`, Redis concurrent) có độ lệch +1.346,868ms ngay request đầu nhưng không limiter error: bước nhảy không đủ để bảo đảm lỗi, phụ thuộc lúc cache được refresh.

## Generator: drop là chính sách bỏ slot cũ

`laterScheduleAlreadyDue` được gọi từ duy nhất vòng schedule trong `internal/experiment/load.go`; sau tăng index, nếu một slot **muộn hơn** đã tới hạn thì bỏ request hiện tại, trước kiểm tra max-inflight. Concurrent miễn nhánh này; cùng timestamp không tự gây backlog. `TestBacklogSkipsOldSlotsButNotSimultaneousBatch` kiểm tra semantics. Ngưỡng max schedule lag trong metadata là 100ms, max-inflight 200.

* Lượt 50: request 054/086/119 (abusive base) lag lần lượt 13,869/13,752/15,465ms, vượt khoảng slot 10ms; request 127 (abusive burst) lag 5,039ms, vượt khoảng slot 5ms. 456/460 request gửi, mỗi API 228; không Redis error.
* Lượt 58: request 192 (abusive burst) lag 6,386ms, vượt khoảng slot 5ms; 459/460 gửi. Redis fallback ở request 178 trước đó, không chứng minh gây drop 192. `scheduled_at` và `end_at` drop này lệch wall clock khoảng 887ms nhưng lag monotonic chỉ 6,386ms.

**Đã chứng minh:** cả 5 drop do scheduler gặp slot tiếp theo đã tới hạn, không phải timeout hay max-inflight. Ba drop xảy ra ở pha base; không nên nói tất cả do tốc độ burst. **Chưa biết:** vì sao timer/scheduler muộn 5–15ms (OS contention, GC, emit JSON dưới mutex, Docker exec sampling đều là khả năng chưa có profile). Không bỏ nhánh backlog chỉ để đủ counts: catch-up sẽ tạo burst giả và đổi workload.

Sampling hiện hữu chạy hai Docker exec INFO cpu/memory rồi sleep 1s, cùng host với generator/API; archive chỉ có 1–2 cặp INFO mỗi lượt bị ảnh hưởng, không có timestamp riêng từng exec hay host CPU. Redis CPU tích lũy không chứng minh peak saturation; không có stats generator, GC hay timer profile. Sampling có thể gây nhiễu nhưng chưa có thí nghiệm đối chứng.

## Bước nhỏ nhất tiếp theo và điều kiện sẵn sàng

1. Giữ nguyên tải và timeout. Thí nghiệm riêng, sau pilot đang chạy: ghi đồng thời wall và monotonic elapsed để phát hiện clock discontinuity; kiểm tra host clock trước so sánh latency/correctness. Không dùng trace wall timestamps cắt pha trực tiếp khi đã phát hiện bước nhảy.
2. Trước sửa dependency, tái hiện stale cache/deadline trong harness độc lập hoặc xác minh sửa upstream tương ứng. Có thể thử socket timeout `-1` (không tự lập deadline từ cache) và giữ context 100ms với `ContextTimeoutEnabled=true`, nhưng phải kiểm tra deadline trên write/read, dial, pool và NOSCRIPT fallback trước áp dụng; đây là đề xuất thí nghiệm chưa kiểm chứng. Không tăng timeout để che triệu chứng.
3. Giữ offered load; chạy đối chứng sampler bật/tắt, cùng workload/repetition, ghi max lag/drop cùng host scheduling nếu cần. Chỉ đổi cơ chế sampling/scheduler khi có bằng chứng; không giảm tải hoặc nới lag để xóa quality flags. Nếu drop tiếp diễn, cải thiện độ ổn định host hoặc generator rồi đo lại cấu hình giữ nguyên.
4. Pilot có clock jump, limiter errors hoặc drops vẫn giữ nguyên evidence và gắn quality flags. Chưa dùng làm benchmark chính thức cho algorithm overhead, scaling hay outage recovery. Đòi hỏi offered-load reconciliation đủ, clocks ổn định và attribution mọi API trước khóa protocol.

Phạm vi fix nếu tiếp tục: Redis client constructor và integration tests, handler context/fail-policy tests; generator Run/callers cmd/loadgen và research-pilot sampling/tests. Không cần tính năng mới, không đổi Lua/quota vì điều tra này chưa chỉ ra lỗi quota algorithm.

Chưa chạy Docker, integration Redis hay tải mới; không sửa runtime/dependency. Nguy cơ còn lại: clock source và causal reproduction chưa được xác nhận, sampler/host scheduling chưa được cô lập.


## Tái hiện độc lập và bản sửa chuẩn bị riêng

Sau điều tra archive, sao chép module đã cài vào `/tmp/project3-redis-drops/go-redis-repro`; không sửa module cache hoặc host clock. [Test tái hiện](deadline-reproduction_test.go.txt) nằm trong package `internal/pool` của bản copy, dừng updater cache rồi đặt cache chậm 1s, gọi **Conn.deadline thực của dependency**, phục hồi cache/updater sau test. Không dùng linkname hay hook unsafe. Lệnh `GOCACHE=/tmp/project3-redis-drops/gocache GOPROXY=off go test ./internal/pool -run '^TestProject3StaleCachedDeadline$' -count=1 -v` PASS: timeout dương 100ms tạo deadline đã hết hạn khoảng **900,148ms**; timeout socket chuẩn hóa bằng 0 giữ đúng context deadline, còn **99,853ms**. Điều này xác nhận cơ chế causal của stale cache; chưa chứng minh trực tiếp ai làm clock nhảy trong lượt lịch sử.

Đã kiểm tra normalization `options.go`: option Read/WriteTimeout `-1` được chuyển thành **0**; `-2` thành **-1**, bỏ thao tác đặt deadline và không phù hợp. Với `ContextTimeoutEnabled=true`, timeout socket 0 vẫn gọi SetRead/WriteDeadline bằng context deadline nguyên bản. Chỉ đổi Read/WriteTimeout sang `-1`, giữ request context, DialTimeout và PoolTimeout 100ms, không retry. Constructor không có Redis operation; mọi call quota từ handler đều có bounded context. Lua/NOSCRIPT dùng chung context.

Bản chuẩn bị trong `/tmp/project3-redis-drops/fix/cmd/server/`: `main.go` dùng helper constructor nhỏ để test đúng cấu hình runtime; `main_test.go` dùng net.Pipe và RESP stub, không mở port hoặc Redis/Docker. Sáu scenario PASS: healthy EVALSHA→NOSCRIPT→EVAL; blocked handshake read; blocked handshake write; blocked command read; blocked command write; blocked NOSCRIPT fallback read. Test assert **mọi socket deadline chính xác bằng context deadline**, options chuẩn hóa đúng, command healthy allow, thao tác blocked kết thúc khoảng 100ms (không gia hạn deadline giữa commands). Lệnh: `GOCACHE=/tmp/project3-redis-drops/gocache GOPROXY=off go test ./cmd/server -run '^TestRedisContextOwnsSocketDeadlines$' -count=1 -v`; 6/6 PASS, tổng 0,510s.

Root áp dụng bản sửa vào `cmd/server/main.go` và regression vào `cmd/server/main_test.go` sau khi pilot 14 lượt kết thúc, giữ nguyên evidence/runtime revision của vòng đó; không thay dependency và không sửa host clock. Cần required checks và calibration sau sửa trước khi xác nhận kết quả thực đo. Dial/pool bounds được giữ và assert ở config, chưa fault-inject dial/pool. net.Pipe xác nhận client I/O deadline, không thay integration Redis/Lua. Client này phải tiếp tục được gọi bằng bounded context; background commands không deadline (ví dụ auth renewal tương lai) sẽ cần context riêng trước khi thêm vào phạm vi prototype.
