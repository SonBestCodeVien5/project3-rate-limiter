# Console: so khớp image content thật — 13/10/2026

**Real comparison được chấp nhận và guard hoạt động; không phải formal gate pass.** Sau fix `7ca8c39`, chạy đúng một triplet none/local/Redis từ checkout sạch `/tmp/project3-postfix-clean` revision `f608873643ed599defe19ede3694338214565318`. Mọi metadata/git-status sạch, workload mixed 120/20 RPS,2 API, 6s, backend 4/50ms, Q=B=20, W=1000ms, r=20/s. Fresh containers/namespace,1s nghỉ sau health, không warm-up; generator timeout 2s/inflight 200; runs tuần tự, browser chỉ sau kết thúc tải. Không rerun gate hoặc sửa host clock/runtime/status/images.

| Mode | Run ID | Sent/scheduled | Legitimate success /120 | Backend overload | 429 | Quality |
| --- | --- | --- | --- | --- | --- | --- |
| None | 20261013T022629-bd56e4d4e3a5 | 720/720 | 48 | 317 | 0 | clocks/fidelity đạt |
| Local FW | 20261013T022713-1011975d376e | 720/720 | 85 | 135 | 323 | clock/fidelity thất bại |
| Redis FW | 20261013T022742-f79870fc9be7 | 720/720 | 103 | 64 | 465 | clocks/fidelity đạt |

Cả ba 0 drops/limiter errors/fallback/transport timeouts. Raw/summary/mọi API/backend reconcile, IDs unique. Local có max sent−scheduled-vs-lag residual 2628,041ms và end−sent-vs-latency2628,040ms, vượt5ms preset; giữ finding, không thay bằng lượt đẹp. None/Redis residual tối đa0,002ms. Oracle none=`not_applicable`,FW=`inconclusive`; không gọi pass. Chỉ là UI integration, không ghép thành kết luận benchmark hoặc tuyên bốmode thắng.

Runner lưu raw `image-inspect.json` trước load và assert exact IDs map vào `images.json`; cả API/backend/Redis/nginx runtime layers/fullConfig/OS/architecture/platform đủ để UI match. Manifest IDs provenance được giữ nguyên. Browser thật chọn ba saved runs: bảng được chấp nhận, số liệu từng lượt hiển thị đúng raw, vẫn ghi oracle chưa đủ bằng chứng. Chấp nhận ở đây chỉ là cấu hình/runtime evidence khớp, không đánh giá clocks hoặc protocol readiness.

Guard tests sử dụng responseclone từ real artifact: Redis workload 120→121RPS bị từ chối `Khác cấu hình: workload`; đổi RootFS layer digest bị từ chối `Khác cấu hình: images`. Không sửa artifact gốc. Phục hồi original responses, bảng lại được chấp nhận. Desktop1280:document scrollWidth1280; mobile390:scrollWidth390,inner table scrollWidth591 (horizontal scroll nằm trongtable container). Screenshots full page và JSON assertions giữ trong archive. Default stack polling dừng sau measurement trong browser; không đổi UI.

[CSV](runs.csv),[JSON](runs.json) giữ offered duration/rate/drain,phase/class lag,drops,errors/backend delta/oracle,max clock residuals,revision/dirty. [Raw archive](evidence/console-content-artifacts.tar.gz),[SHA256 manifest](evidence/manifest.json) bỏ loadgen binary,portable paths dưới artifacts/console-content-20261013; checksum từng member đã xác nhận. Raw ở `artifacts/console-content-20261013/`; clean checkout vẫn giữ original Console artifacts. Original pilot/postfix archive không thay đổi.

Console đã dừng; owned Docker project không còn container, chỉ postgres unrelated giữ nguyên. Không commit.

Không rerun formal gate. Rủi ro: host clock vẫn nhảy ở local run, FW partial window inconclusive, 3×6s chỉ kiểm tra UI chứ không đủ kết luận nghiên cứu.
