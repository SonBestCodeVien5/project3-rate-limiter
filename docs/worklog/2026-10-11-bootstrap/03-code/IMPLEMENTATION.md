# Kết quả code và tổ chức công việc

## Thành phần

| Mã | Vai trò |
| --- | --- |
| `internal/limiter` | Policy, local mutex FW/TB, Redis Lua FW/TB, unit/integration tests |
| `internal/server`, `cmd/server` | API middleware, fail policies, backend semaphore, metrics và lifecycle |
| `internal/experiment`, `cmd/loadgen` | Generator open-loop, trace JSONL, metadata và summary |
| `Dockerfile`, `compose.yaml`, `deploy/nginx.conf` | Testbed loopback với 2 API, Redis, backend và LB |
| `scripts` | Verify pipeline, mixed pilot, outage, cleanup tests và hướng dẫn |

Thiết kế chi tiết: [IMPLEMENTATION](../../../IMPLEMENTATION.md). Thông số trong Compose là mặc định pilot, không phải nguồn requirement.

## Phân công agent

Theo quyền người dùng cho phép tạo agent: agent chính xử lý context, policy/limiter, integration, tài liệu và commit; agent HTTP/infra xử lý API/backend/hạ tầng; agent experiments xử lý generator/runner; agent review đọc độc lập và gửi findings. Các agent phụ không commit; agent chính stage theo phần và kiểm tra tích hợp.

Prompts và hướng dẫn agent dùng tiếng Anh theo AGENTS.md; tài liệu báo cáo/người dùng dùng tiếng Việt. Không dùng skill sync vì không có yêu cầu sync hoặc bằng chứng Drive đổi. Nguồn kỹ thuật bổ trợ: Redis Lua/TIME docs và go-redis qua Context7, không thay thế yêu cầu dự án.

## Quyết định quan trọng khi code

- POST giữa generator → API → backend và Nginx tắt retry để tránh tự lặp quota/backend work khi lỗi connection.
- Redis command retry tắt; timeout không chứng minh script chưa chạy.
- API xác nhận backend arrival từ header backend; lỗi transport ghi `unknown`; counter backend dùng để đối chiếu.
- Không đưa biến thể Redis không atomic vào API config; test barrier minh họa lỗi trong phạm vi hẹp.
- Runner không tự commit/push hoặc sửa protocol. Workflow phát triển có bước review và stage rõ ràng trước commit.
