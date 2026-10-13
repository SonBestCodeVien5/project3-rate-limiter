# Hiệu chỉnh HTTP ngày 13/10/2026

**Chưa sẵn sàng khóa bộ đo chính thức:** đã có cấu hình normal/mixed hữu ích và bằng chứng HTTP cho local Token Bucket sau sửa, nhưng clock host nhảy trong 3 lượt và healthy Redis còn 2 I/O timeout. Giữ toàn bộ lượt, không chỉnh ngưỡng để lấy kết quả đẹp. Không sửa runtime, không commit, không chạy lại ma trận84 hoặc thí nghiệm chính thức.

Tiêu chí và thứ tự ghi trước tải trong [PRESET](PRESET.md), dựa trên [protocol ứng viên](../../experiments/PROTOCOL_CANDIDATE.md). Đây là lựa chọn hiệu chỉnh kỹ thuật, không phải tham số nguồn yêu cầu. Chạy tuần tự 6 cell×2 lượt CLI và một run Console×2 lượt, mỗi lượt6s offered load, state/container/namespace mới, chờ1s sau health không warm-up. Q=B20,W1000ms,r20/s; timeout2s,inflight200; 5 key hợp lệ, một key bất thường. Revision runtime ghi `72c3c17b70437bf3d5cfe09d3e9c11384e5f3354`; trạng thái dirty từng lượt được giữ trong metadata/git-status. Không làm thay đổi archive ngày12/10.

| Nhóm | Cấu hình | Kết quả từng lượt |
| --- | --- | --- |
| Historical local TB mixed | 2API,120/20RPS,backend10/50ms | 720sent/lượt,0drops/0limiter errors,oracle không thấy violation; lượt1 clock không ổn,lượt2 đạt fidelity |
| Historical local TB burst | 1API,nền120/20RPS,abusive200 tại1–2s,backend10/50ms | 820sent/lượt,0drops/0errors,oracle không thấy violation; lượt1 clock không ổn,lượt2 đạt fidelity |
| Normal Redis FW | 2API,20RPS toàn hợp lệ,backend4/50ms | 120/120 legitimate successful mỗi lượt,0reject/overload/error/drops; p95=54,21/54,22ms |
| Mixed none | 2API,120/20RPS,backend4/50ms | legitimate successful48/51 trên120,backend overload314/313; fidelity đạt |
| Mixed local FW | Cùng tải/backend/topology mixed | legitimate successful89/82,overload138/136; fidelity đạt |
| Mixed Redis FW | Cùng tải/backend/topology mixed | legitimate successful105/104,overload69/68; lượt1clock nhảy và2fail-closed/errors; lượt2fidelity đạt,0errors |
| Console normal Redis FW | Cùng normal,2repeats | 120success mỗi lượt,0reject/overload/error/drops; p95=54,46/53,73ms; maps summary/analysis1/2 khớp raw và browser chọn đúng KPI |

14 lượt hoàn tất,7.880sent=scheduled,0drops,3.569HTTP2xx,3.271HTTP429,1.040HTTP5xx. Đây là tổng kiểm kê nhiều workload, không dùng xếp hạng. Toàn bộ request IDs unique; summary/trace, mọi API requests/rejected và backend arrivals/success/overload/canceled reconcile bằng assert trong [summarize.py](summarize.py). Không transport timeout. 4TB oracle=`no_violation_observed_within_trace`; 8FW=`inconclusive`; 2none=`not_applicable`. Inconclusive không pass. Hai lượt TB lần2 có clocks/fidelity ổn cho bằng chứng runtime về sửa float; không suy thành chứng minh mọi workload không lỗi. Local2API vẫn cho quota chung vượt single bucket do state riêng, là semantics đã biết.

## Fidelity và clock blocker

P95 schedule lag toàn lượt1,13–2,03ms, trong các ngưỡng preset và khoảng gửi5/10/50ms. RPS ghi trên CSV dùng sent/6s offered duration, không dùng thời gian drain làm mẫu số; JSON ghi phase/class actual wall sends và p95lag riêng, send span, elapsed monotonic gồm drain, wall elapsed và delta hai clock.

Ba lượt `tb-mixed2/repeat1`, `tb-burst1/repeat1`, `mixed-redis/repeat1` có wall elapsed lớn hơn monotonic lần lượt **2,717/2,706/2,526s**. Ví dụ mixed TB: start08:53:43,223+07, ended08:53:51,984+07 (wall8,761s), summary elapsed6,044s; request cuối scheduled08:53:49,213, sent08:53:51,932 nhưng schedule_lag0,960ms. Đây là evidence clock wall/monotonic không liên tục, không phải bằng chứng generator âm thầm tăng tốc hoặc backend pause. Căn nguyên host/WSL/synchronization chưa được kết luận. Loại khỏi phép so performance khỏe liên quan theo clock-stability/fidelity preset; giữ oracle outcome có giới hạn. Sau hai lần thấy cùng blocker không chạy thêm replacement chỉ để kiếm lượt đẹp. `>10ms` trong script chỉ là detector chênh wall/monotonic, không nới/đổi ngưỡng fidelity đã ghi trước.

Redis mixed repeat1 có2errors ởAPI2; log `write tcp ... i/o timeout` và `Redis quota decision: i/o timeout`, cả hai fail-closed. Cùng lượt clock nhảy nhưng chưa chứng minh quan hệ nhân quả. Chưa dùng lượt này kết luận healthy Redis overhead. Những lượt Redis khác0errors không xóa finding này.

## Khuyến nghị và giới hạn

Giữ ứng viên normal20RPS/all legitimate5keys (4RPS/key),Q20,backend4/50ms: đo đủ120success/lượt, không overload. Giữ mixed120total/20legitimate,backend4/50ms cho so mode: no limiter gây overload và giảm success hợp lệ từ120 xuống48–51. Local/Redis giảm overload trong pilot matched này; p95 chỉ tính request thành công nên không che mất availability. Redis khỏe chỉ còn một lượt mixed hợp lệ, chưa đủ kết luận độ biến thiên. Các mức sweep scaling,30s/3repeats,atomicity/outage/recovery vẫn cần khóa riêng sau xử lý clock/Redis blocker; không chạy formal trong host chưa ổn định.

Console kiểm tra API thật, hai summary/analysis tách lượt, browser đổi selector1/2 cho p95 khác nhau đúng artifact. Browser polling có overhead, run Console là demo validation, không ghép vào so overhead CLI. Request đầu bị400 vì gửi mixed_rps cho custom; sửa đúng contract thành0, không có load/container từ request bị reject; giữ lỗi trong evidence. Không dựng stack mặc định; lỗi browser kết nối stack mặc định không liên quan research run.

## Artifact và cleanup

- [CSV từng lượt](runs.csv),[JSON với phase/class](runs.json).
- [Raw archive](evidence/calibration-artifacts.tar.gz),[SHA256 manifest](evidence/manifest.json):424files, portable paths dưới artifacts/calibration-20261013, bỏ loadgen binary; đã giải đọc từng member và xác nhận checksum.
- [Lệnh CLI đã dùng](run-calibration.sh),[Console HTTP assertions](console-validation.py),[derivation/assertions](summarize.py). Chạy lại cần output mới; không ghi đè raw archive.
- Raw đang giữ thêm ở `artifacts/calibration-20261013/`, Console run `artifacts/console/20261013T020106-009081922389/`. Console đã dừng; docker owned project không còn container; trước/sau chỉ còn unrelated `fast_api_learn_postgres postgres:17`, không đụng tới nó. Không prune/delete image hoặc artifact cũ.

Bỏ qua formal sweep/outage và thay đổi runtime. Rủi ro còn lại: clock host/Redis timeout chưa rõ nguyên nhân,FW oracle chưa đủ cửa sổ,2×6s chưa đủ suy luận thống kê hoặc production.
