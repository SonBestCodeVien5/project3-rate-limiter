# Điều tra hai local Token Bucket mismatch — 13/10/2026

Đây là sửa lỗi kỹ thuật cho pilot, không khóa protocol hay xác nhận benchmark nghiên cứu. Phạm vi theo [Roadmap nguồn](../../context/sources/00_Project3_Roadmap.md): quyết định quota đúng và đo được. Evidence gốc là [ma trận ngày 12/10](../2026-10-12-console-matrix/README.md), không được sửa hoặc thay bằng kết quả replay.

## Nguyên nhân và bằng chứng

Hai lượt đều có lỗi reject tại biên refill do cộng dồn số thực trong local limiter. Không tìm thấy lỗi chuyển timestamp trong hai trace: thời gian quyết định đến từ `Decision.At` của limiter, được server đưa nguyên qua `X-Decision-Time`; local limiter và oracle cùng dùng Unix milliseconds. Hai nhóm abusive có finding không có timestamp trùng nhau. Replay công thức float cũ, theo từng `(client_key, instance)`, khớp **toàn bộ quyết định quan sát được** của cả hai lượt.

| Run ID | Finding đầu tiên (Unix ms) | Token trước quyết định theo float cũ | Finding trong trace khi dùng oracle chính xác |
| --- | ---: | ---: | ---: |
| `20261012T025545-ea44194c1d29` | 1791773761561 | 0.9999999999999976 | 27 |
| `20261012T030353-a2b3f479b6a3` | 1791774248110 | 0.9999999999999938 | 20 |

Finding đầu tiên đều thuộc `abusive-0001` / `api-1`, request tương ứng `custom-repeat-1-000000140` và `custom-repeat-1-000000080`. Policy là B=20, r=20/s. Toán học cho phép một request ở biên đủ token, nhưng float cũ nhỏ hơn 1 nên reject; đây là **under-admission**, không phải overshoot đã xác nhận. Replay mới tại đúng các timestamp quan sát được thay đổi 54 và 40 quyết định allow/reject, chủ yếu dịch quyết định allow về đúng biên; không phải 54/40 request bổ sung được phép.

Ca tối thiểu độc lập: B=1, r=20/s; allow tại 0ms làm cạn bucket, reject tại 3ms và 32ms, rồi phải allow tại 50ms. Float cũ cộng `0.06 + 0.58 + 0.36 = 0.9999999999999999` và reject sai. Regression Go bao gồm ca này, rate phân số 2.5/s, Remaining và RetryAfter.

Oracle cũ dùng `floor(tokens + 1e-10)`, cũng có thể kỳ vọng allow **sớm** nếu token thực chỉ hơi thiếu 1. Ca độc lập B=1, r=999.99999995/s, cạn tại 0ms: tại 1ms còn 0.99999999995 token nên phải reject. Regression Python giữ cả ca thiếu token này và reject sai tại đúng biên.

## Thay đổi nhỏ nhất

* `internal/limiter/local.go`: giữ token nội bộ theo milli-token, refill bằng `elapsed_ms * rate`, tiêu thụ 1000 đơn vị/request. Integer rate trong phạm vi policy có phép tính chính xác khi state chưa đầy; không nới ngưỡng allow. Remaining/RetryAfter vẫn xuất theo đơn vị cũ; mutex, expiry và rollback không đổi.
* `scripts/analyze.py`: dùng `fractions.Fraction` của thư viện chuẩn cho replay quyết định, với rate theo giá trị thập phân policy, bỏ epsilon ở ngưỡng allow. Vẫn gộp allow count tại cùng millisecond. Điều kiện trace thiếu, fallback, outage, hủy run và state reset vẫn giữ nguyên.
* `internal/limiter/local_test.go`, `scripts/test_analyze.py`: regression biên refill, rate phân số và ngưỡng thật sự thiếu token.

Phạm vi caller đã đọc: server truyền quyết định/remaining/retry/time, load generator thu response headers, oracle và các test local/Redis/analyzer. Không đổi interface, schema, policy hoặc dependency.

## Kiểm chứng và tái kiểm tra

Archive SHA256 vẫn là `60aed17a9ea0688b425abe82bab3179ff841d558b27dd3f8ae0e7b8902f19b9d`. Giải nén vào `/tmp/project3-token-bucket-investigation`, chỉ ghi `analysis.*` trong bản giải nén. SHA256 của requests.jsonl lần lượt là `f2ac8624d1e49d7e561b55d5abd2e3249fc378f2c9a753ab4c19bc2bd1df3597` và `011307ffa77fac507a575444534b923a2153c320f362b501d98e4029f72b77ab`.

```bash
mkdir -p /tmp/project3-token-bucket-investigation
tar -xzf docs/worklog/2026-10-12-console-matrix/evidence/console-matrix-artifacts.tar.gz -C /tmp/project3-token-bucket-investigation
python3 scripts/analyze.py /tmp/project3-token-bucket-investigation/artifacts/console/20261012T025545-ea44194c1d29/result/custom-repeat-1
python3 scripts/analyze.py /tmp/project3-token-bucket-investigation/artifacts/console/20261012T030353-a2b3f479b6a3/result/custom-repeat-1
GOCACHE=/tmp/project3-token-bucket-investigation/go-cache go test ./internal/limiter
python3 -m unittest discover -s scripts -p test_analyze.py
```

Kết quả: limiter tests (bao gồm `go test -race ./internal/limiter`) và 17 analyzer tests pass; hai bản trace gốc **vẫn `observed_violations`**, 27/20 findings. Không chuyển historical findings thành pass. Một test Go tạm được sinh từ tất cả 18 nhóm key/instance của hai trace, rồi xóa sau chạy: local limiter mới khớp oracle Fraction tại mọi timestamp. Trace quyết định sinh từ replay mới không có violation; đây là kiểm chứng thuật toán với lịch đến cũ, không phải lượt đo HTTP mới. Script replay phục vụ điều tra nằm tại `/tmp/project3-token-bucket-investigation/replay.py`.

## Giới hạn

Không chạy lại ma trận 84 lượt, không đo performance sau sửa, không điều tra Redis timeout hoặc sửa Lua Redis. Các trạng thái inconclusive trong hồ sơ cũ vẫn giữ nguyên. Millisecond replay không chứng minh thứ tự wall-clock khi server clock rollback; hai trace này không cho thấy rollback. Rate phân số bất kỳ vẫn được local biểu diễn bằng float64, nên milli-token không bảo đảm mọi biên thập phân đều chính xác; oracle Fraction sẽ tiếp tục phát hiện lệch nếu có evidence. Cần lượt đo mới trước khi kết luận chất lượng runtime hoặc throughput sau sửa.
