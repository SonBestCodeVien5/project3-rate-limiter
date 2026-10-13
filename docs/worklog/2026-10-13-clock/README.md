# Quan sát wall clock độc lập — 13/10/2026

Quan sát read-only nhẹ khoảng 20Hz, 1796 mẫu trong 90.020540s monotonic. Wall clock trôi qua 95.264676s: tổng chênh lệch +5,244135s. Không chạy Docker/test tải, không chỉnh clock/NTP, không sửa repo. Python sleep 50ms giữa mẫu; mỗi mẫu chỉ đọc monotonic/realtime và giữ ba integers trong RAM, ghi output một lần sau quan sát.

| UTC sau bước nhảy | Delta realtime (ms) | Delta monotonic (ms) | Real − mono (ms) |
| --- | ---: | ---: | ---: |
| 2026-10-13T02:09:35.256342+00:00 | 2678.873141 | 50.113244 | +2628.759897 |
| 2026-10-13T02:10:10.360520+00:00 | 2665.508308 | 50.132990 | +2615.375318 |

Hai bước tiến wall clock khoảng +2,6s đã được quan sát thực, trong khi khoảng lấy mẫu monotonic vẫn khoảng 50ms. Điều này xác nhận discontinuity realtime đang xảy ra trên môi trường chung ngay cả khi observer không tạo tải. Không phải chỉ suy luận từ timestamp archive. Span đọc một mẫu tối đa 161.959µs, nhỏ hơn nhiều bước nhảy. Không có step khác vượt ngưỡng 5ms trong cửa sổ này. Đây là bằng chứng clock instability; không quy nguyên nhân cho workload đang chạy đồng thời.

Host dùng kernel `6.18.40.1-microsoft-standard-WSL2`, `systemd-detect-virt` báo `wsl`; clocksource đang dùng `tsc`, có các nguồn `hyperv_clocksource_tsc_page`, `hyperv_clocksource_msr`, `acpi_pm`. timedatectl read-only không truy cập bus được (`Operation not permitted`); chronyc và ntpq không có. Chưa biết trạng thái NTP, không có Windows host clock/event log hay hypervisor diagnostic. **Nguồn điều chỉnh clock vẫn chưa xác định**; WSL2 là môi trường quan sát được, chưa chứng minh WSL/NTP/Windows là tác nhân cụ thể.

Artifacts: `observe.py`, `samples.jsonl`, `summary.json`, `environment.json`, `sha256.json` trong cùng thư mục. CLOCK_REALTIME được so với CLOCK_MONOTONIC; dùng midpoint hai lần đọc monotonic để hạn chế sai số đo. Chưa kiểm chứng đồng hồ trong từng container; không Docker. Bước nhảy toàn cục host quan sát được đủ để tiếp tục giữ clock-discontinuity quality flag và chưa khóa protocol dựa trên wall timestamps. Socket mitigation vẫn cần post-fix gate riêng; observer này không đo hiệu năng Redis hoặc chứng minh hiệu quả mitigation.
