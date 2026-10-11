# Kế hoạch vòng 2: hoàn thiện công cụ đo

## Yêu cầu và đầu vào

User yêu cầu tiếp tục triển khai tự động, điều phối subagent GPT-6 Sol medium cho phần phù hợp, giữ commit nhỏ, đồng thời đánh giá tiến độ/phạm vi và cách học sau khi dựng prototype. Điểm xuất phát `c859fef`, working tree sạch, 10 commit bootstrap. Đã đọc brief → SOURCE_INDEX → Roadmap → Proposal → Research/Positioning và trạng thái hiện tại. Không có bằng chứng Drive thay đổi; không sync lại notes.

## Phạm vi lần này

1. Generator: thêm normal, burst có pha hữu hạn, batch concurrent; giữ mixed cũ, POST, lịch open-loop, giới hạn bộ nhớ/in-flight, drops và actual send lag.
2. Topology và runner: render 1/2/4 API instance cùng backend cố định, LB đúng topology; case metadata/policy thật từ config resolved; pilot hữu hạn có lặp lựa chọn và cleanup.
3. Analyzer độc lập: quota theo policy/thời điểm server, phân biệt local/global, FW vs TB; báo inconclusive khi thiếu bằng chứng, không biến timeout/fallback thành pass; phases outage, legitimate availability và recovery có tiêu chí rõ.
4. Kiểm thử synthetic và pilot end-to-end, review chéo, recode/retest, commit theo module. Giữ raw data/config, nguồn code và logs tái lập.
5. Đánh giá scope/tiến độ và hướng tự học trong tài liệu riêng. Tỷ lệ hoàn thành là ước lượng quản trị theo nhóm deliverable, không phải rubric trường hoặc đo bằng số dòng code.

## Những gì chưa tự tuyên bố hoàn tất

Protocol chính thức chưa khóa, chưa đủ dữ liệu lặp để kết luận RQ1–RQ5, chưa xác nhận kiến thức của người học. Không mở rộng gateway/dashboard/HA chỉ vì code nhanh. Pilot mới là dữ liệu kiểm chứng công cụ, chưa thay bộ benchmark cuối kỳ.

## Phân công

- `workload_v2`: Go generator/CLI/tests; model GPT-6 Sol medium.
- `topology_v2`: render topology, runner, protocol candidate/tests; model GPT-6 Sol medium.
- `analysis_v2`: Python stdlib analyzer/tests và assumptions; model GPT-6 Sol medium.
- Phiên chính: thống nhất contract, đối chiếu nguồn/phạm vi, review các giả định ảnh hưởng nghiên cứu, chạy tích hợp và điều phối commit. Agent không tự push.

## Contract và rủi ro

Raw trace thêm phase, giữ đọc được dữ liệu bootstrap. Policy JSON do runner xuất từ config thật; label ở CLI không tự chứng minh server config. Mọi claim correctness cần trạng thái đầu đã biết và trace đầy đủ; request timeout có thể đã tiêu quota. TB không dùng Q/W của FW để kết luận overshoot. Batch cùng lịch không đồng nghĩa request tới Redis cùng thời điểm. Warm-up nếu chưa có phải ghi rõ cold-start, không giấu trong số liệu. Runner phải giữ backend capacity/service time khi đổi số API.

## Điều kiện hoàn tất vòng

Tests có ý nghĩa PASS; topology 1/2/4 render đúng; chạy đại diện profile/topology và analyze raw được; mọi finding chặn đã sửa/retest; docs phản ánh đúng code; evidence và git history chia phần rõ; git status sạch. Công việc nghiên cứu chính thức còn lại được ghi cụ thể.
