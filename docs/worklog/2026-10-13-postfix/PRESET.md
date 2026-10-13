# Kiểm chứng sau sửa deadline Redis — ghi trước tải

Đây là pilot kiểm tra điều kiện chuyển sang benchmark, chưa phải dữ liệu chính thức. Người dùng cho phép tự động tiếp tục ngày 13/10/2026; các giá trị là lựa chọn kỹ thuật dựa trên calibration, không phải yêu cầu nguồn hoặc phê duyệt của giảng viên.

Chạy tuần tự tối đa 6 lượt: normal Redis Fixed Window 3 lượt, rồi mixed Redis Fixed Window 3 lượt. Mỗi lượt 30s offered load, 2 API, 5 client hợp lệ; Q=B=20, W=1000ms, r=20/s; backend capacity4/service50ms. Normal 20 RPS toàn hợp lệ; mixed tổng120/20 RPS hợp lệ. Fresh containers/namespace từng lượt, 1s chờ sau health không có warm-up tải; timeout Redis/request100ms giữ nguyên, generator2s/inflight200, sampler hiện có bật.

Tiêu chí đặt trước: 0 drops; scheduled=sent và raw/summary/counters mọi API/backend reconcile; không có healthy Redis fallback/limiter error; per-phase/class offered rate trong ±5%; p95 schedule lag ≤10ms và ≤khoảng gửi của luồng. `abs(wall(sent−scheduled)−monotonic schedule_lag)` và `abs(wall(end−sent)−monotonic latency)` tối đa5ms; clock discontinuity làm lượt không đủ cho so performance/oracle theo thời gian. FW partial-window inconclusive không tự loại lượt, nhưng không là correctness pass. Normal không có reject hoặc backend overload; mixed phải có outcomes được attribution, không loại vì overload chủ ý.

Giữ mọi lượt và quality flags; không thay timeout/tải/ngưỡng hoặc chọn subset đẹp. Nếu cùng blocker clock/fidelity/healthy Redis error xuất hiện ở hai lượt, dừng gate, không chạy tiếp ma trận chính thức. Các lượt chưa chạy ghi rõ chưa thực hiện. Nếu tất cả 6 lượt đạt, vẫn cần calibration scaling/burst/outage và khóa manifest/protocol trước bộ chính thức. Không sửa host clock hoặc container unrelated.

Sau gate có thể kiểm tra UI bằng dữ liệu đã lưu, tạo bảng/biểu đồ pilot có giới hạn và kiểm tra Redis integration riêng; không chạy chúng đồng thời với phép đo. Revision/git-status/image identity thực tế phải lưu từng lượt. Archive nguyên bản và checksum cần được lưu cùng hồ sơ.
