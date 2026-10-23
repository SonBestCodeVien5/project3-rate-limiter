# Học monitoring từ prototype rate limiter

Mục tiêu là tự giải thích và kiểm tra được pipeline monitoring trước bảo vệ, đồng thời có nền cho đồ án tốt nghiệp. **Chưa có xác nhận người học hoàn thành các nội dung dưới đây.** Task kỹ thuật ở [kế hoạch P2](PHASE2_PLAN.md), việc baseline ở [kế hoạch chung](../REMAINING_WORK_PLAN.md), thiết kế ở [DESIGN.md](DESIGN.md), thao tác dự kiến ở [RUNBOOK.md](RUNBOOK.md); quy tắc đo nghiên cứu vẫn theo [readiness](../experiments/PROTOCOL_READINESS.md).

## 1. Mạch học gắn với bài toán

Traffic flash sale là bối cảnh giả định. Pain point là client hợp lệ cùng cạnh tranh tài nguyên với traffic gây quá tải; tác động kinh doanh là giả thuyết, không phải doanh thu đã đo. Yêu cầu kỹ thuật là kiểm soát request trước backend và quan sát được quyết định trên nhiều API instance. Limiter xử lý traffic, monitoring giúp nhìn và giải thích diễn biến; thí nghiệm/trace mới là nơi kiểm chứng kết luận nghiên cứu.

Học theo thứ tự instrumentation → scrape → time series/PromQL → dashboard → logs/LogQL → chẩn đoán sự cố → vận hành có giới hạn. Không cần học cả hệ sinh thái observability cùng lúc.

## 2. Các mốc tự kiểm tra

Chỉ người học xác nhận cột cuối bằng lời giải/thao tác thực tế. Agent có thể ghi đã giải thích hoặc đã chạy test, không tự suy thành “đã hiểu”.

| Mốc | Gắn với task | Bài tập / câu hỏi | Xác nhận hiện tại |
| --- | --- | --- | --- |
| L1 — nguồn dữ liệu | P2-01 | Theo một request từ API tới backend; chỉ chính xác nơi tăng requests, rejected, attempts, arrivals và success | Chưa xác nhận |
| L2 — metric types/labels | P2-01/P2-02 | Counter khác gauge thế nào? Khi restart thì sao? Vì sao client ID làm tăng số series? | Chưa xác nhận |
| L3 — scrape và PromQL | P2-03 | Đọc `up`, viết rate theo API, tổng reject/s; giải thích vì sao rate trước sum và thiếu mẫu khác 0 | Chưa xác nhận |
| L4 — dashboard kể chuyện | P2-03/P2-06 | Chỉ ra traffic vào, 429, backend overload; phân biệt quan sát với giả thuyết | Chưa xác nhận |
| L5 — logs và pipeline | P2-04/P2-05 | Từ stdout qua Alloy tới Loki; viết query theo service và message; giải thích indexed label so với JSON field | Chưa xác nhận |
| L6 — chẩn đoán | P2-05/P2-07 nếu làm | Vì sao API UP khi Redis lỗi? Phân biệt lỗi app, lỗi dependency và lỗi telemetry | Chưa xác nhận |
| L7 — vận hành/tái lập | P2-08 | Dựng bằng config repo, kiểm tra state/retention, dừng đúng project và giải thích quyền socket | Chưa xác nhận |
| L8 — phương pháp nghiên cứu | P2-06/P2-08 | Vì sao dashboard không chứng minh quota đúng, không thay trace/T10, và không tự cho biết goodput hợp lệ? | Chưa xác nhận |

## 3. Bài tập nhỏ, không cần tạo tải mới

Các bài tính tay và đọc code có thể dùng trước khi được phép runtime:

1. Counter của API1 tăng từ 100 lên 140 trong 10s, API2 từ 80 lên 100 trong 10s. Tính mức tăng trung bình từng API và tổng; chỉ ra vì sao đây chưa phải mô tả đầy đủ thuật toán extrapolation của PromQL.
2. API restart làm counter từ 140 về 3. Giải thích vì sao lấy hiệu trực tiếp sẽ sai, và vì sao nên xử lý rate từng series trước khi cộng.
3. 10 request tới backend, 3 overload, 7 xử lý thành công. Giải thích vì sao arrivals đã chứa các lượt có kết quả này, và vì sao chưa biết có bao nhiêu client hợp lệ nhận 2xx.
4. Mode none có 100 backend attempts nhưng allowed=0. Đọc nhánh `h.limiter != nil` để giải thích, không sửa metric để làm khớp suy đoán.
5. Một target không có sample và một target có counter không tăng. Chọn cách hiển thị khác nhau, tránh làm mất thông tin lỗi telemetry.
6. So sánh ba logs `server started`, `limiter unavailable`, `server stopped`: mỗi log chứng minh điều gì và không chứng minh điều gì?

Sau G2/G3 mới làm bài thực hành: tự mở target, query một metric, tìm log startup, chọn đúng time range một case và giải thích một điểm dữ liệu. Không yêu cầu chạy lại benchmark để học cách bấm Grafana.

## 4. Cách giải thích khi bảo vệ

- **Vấn đề:** traffic tăng có thể làm backend giới hạn năng lực từ chối request, ảnh hưởng cả client hợp lệ.
- **Yêu cầu:** kiểm soát traffic trên nhiều API và quan sát request bị giới hạn hoặc đi tiếp.
- **Giải pháp:** limiter local/shared Redis; Prometheus lấy metrics, Alloy đưa logs tới Loki, Grafana hiển thị.
- **Demo:** nói rõ mode, policy, workload, topology, khoảng thời gian và đây là telemetry minh họa mới.
- **Đánh giá:** chỉ diễn giải những đường/sự kiện thực sự có dữ liệu; T10 là bộ kết quả nghiên cứu riêng với giới hạn đã ghi.
- **Hướng tiếp theo:** chọn một nhu cầu cụ thể như theo dõi độ trễ client hợp lệ; giải thích instrumentation còn thiếu trước khi đề xuất thêm công cụ.

Các câu cần tự trả lời: 429 tăng có luôn xấu không? Backend success tăng có đồng nghĩa người mua hợp lệ được phục vụ tốt hơn không? Local quota ở hai instance có nghĩa gì? Lua atomicity được bảo đảm ở đâu? Một biểu đồ sampled có đủ chứng minh không overshoot không? Log warning dày là nhiều incident hay nhiều request gặp cùng incident?

## 5. Kiến thức chuyển tiếp sang đồ án tốt nghiệp

| Nền tảng từ P2 | Có thể dùng tiếp khi xuất hiện nhu cầu | Chưa được tuyên bố đã làm |
| --- | --- | --- |
| Định nghĩa metric, mẫu số và labels | Thiết kế service-level indicators (SLI) gắn với trải nghiệm người dùng | Chưa có SLO/SLA hoặc alert policy production |
| PromQL và dashboard có nguồn rõ | Theo dõi capacity, error rate và độ trễ theo loại request | Chưa có histogram/client-class instrumentation |
| Thu logs có scope và truy vấn JSON | Điều tra sự cố nhiều service, correlation khi có ID phù hợp | Chưa có tracing hay correlation end-to-end |
| Config/provisioning trong Git | Tái lập môi trường và review thay đổi monitoring | Chưa có cloud deployment, CI/CD observability hoặc HA |
| Giới hạn quyền và storage | Cân nhắc collector permissions, retention và chi phí dữ liệu | Chưa kiểm định an toàn/hiệu năng production |

Alerting, histogram và tracing là những bài học tiếp theo có thể chọn sau P2, không phải checklist phải triển khai ngay để hoàn tất đồ án hiện tại.

## 6. Nguồn học tối thiểu

Đọc code và bài tập trước, sau đó đọc đúng phần vendor docs:

- [Metric types](https://prometheus.io/docs/concepts/metric_types/), [instrumentation practices](https://prometheus.io/docs/practices/instrumentation/).
- [PromQL basics](https://prometheus.io/docs/prometheus/latest/querying/basics/), [query functions](https://prometheus.io/docs/prometheus/latest/querying/functions/).
- [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).
- [Alloy Docker log source](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/).
- [Loki labels/cardinality](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/), [LogQL](https://grafana.com/docs/loki/latest/query/).

Nguồn API/config phải đối chiếu phiên bản thực tế lúc triển khai. Không cần đọc hết tài liệu vendor hoặc cài thêm stack khác để hoàn thành từng mốc học.
