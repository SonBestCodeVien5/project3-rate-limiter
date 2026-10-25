# Giới hạn và điều kiện tiếp tục

- No-load registration dùng trực tiếp render-topology.py và console-monitoring.py dưới artifacts/.research-pilot.lock; các record có trạng thái incomplete có chủ đích vì không gửi workload.
- Chưa chạy research-pilot.sh / nút Console Chạy benchmark; chưa xác minh đăng ký trước tải, log trong/sau workload, final scrape sau drain, cleanup khi cancel/SIGTERM hoặc phục hồi stale manifest sau sự cố. Các tiêu chí này cần G3/Console runner lifecycle riêng.
- Chưa chạy P2-06, P2-07/G4, P2-08; chưa có xác nhận học tập từ người dùng.
