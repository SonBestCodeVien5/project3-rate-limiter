# Demo Project3 — khoảng 6 phút

Đây là kịch bản demo prototype kèm kết quả T10 đã phân tích offline từ benchmark chính thức; saved-run UI dùng ba lượt pilot ngày 13/10. Không trình bày pilot UI như kết quả benchmark chính thức. Xem [kết quả T10](analysis/T10_RESULTS.md), [trạng thái sẵn sàng](experiments/PROTOCOL_READINESS.md) và [trạng thái công việc](REMAINING_WORK_PLAN.md). Chuẩn bị trước để không phụ thuộc tải trực tiếp. T13 chưa có deck: Canva import bị HTTP 429 trước design ID; chưa rehearsal thực tế. Rubric, feedback, ngày chính thức và nguồn học thuật cuối còn chờ.

**Nhánh giai đoạn 2 (23/10/2026):** P2-03 đã kiểm tra stack monitoring cố định và dashboard. Nút Console `Gửi một request mẫu` đi qua cùng ingress; nút **Chạy benchmark** vẫn tạo project `project3-research-lab`, không hiện trên dashboard. Luồng Console chạy demo tải trên stack cố định là đề xuất P2-03A, chưa triển khai/cấp quyền. Xem [registry P2](monitoring/PHASE2_PLAN.md) trước khi thêm thao tác; giữ telemetry demo mới, pilot Console và kết quả T10 riêng biệt.

| Thời gian | Nội dung / thao tác |
| --- | --- |
| 0:00–0:45 | Flash sale giả định: traffic tăng, backend có năng lực giới hạn, người mua hợp lệ bị ảnh hưởng. Nêu rằng prototype mô phỏng API, không xây hệ thống bán hàng. |
| 0:45–1:30 | Vẽ luồng client → LB → API limiter → backend dùng chung; mỗi API có local state riêng, còn Redis cung cấp shared state cho các API và Lua bảo đảm atomicity. Quota tính theo key; FW và TB có cách xử lý burst khác nhau. |
| 1:30–3:00 | Mở Console, chọn bộ ba saved-run pilot none/local/Redis cùng cấu hình từ 13/10. Chỉ ra goodput/p95/p99 của client hợp lệ, 429, 5xx và request backend nhận/quá tải; nói rõ bảng UI này chỉ kiểm tra artifact/runtime pilot. Mở [bảng/kết quả T10](analysis/T10_RESULTS.md) và các hình/bảng đã lưu để trình bày kết quả benchmark chính thức. Nếu giao diện từ chối ghép lượt, giải thích nguyên nhân và mở artifact thay vì ép chấp nhận. |
| 3:00–4:00 | Mở policy/Compose đã resolve, summary/analysis và trace. Chuyển lượt để cho thấy KPI không chỉ lấy repeat1. Trạng thái oracle `inconclusive` nghĩa là chưa đủ bằng chứng kết luận; runner hoàn tất không đồng nghĩa tính đúng đã đạt. |
| 4:00–5:00 | Trình bày hai sửa lỗi lịch sử: local TB từ chối do sai số float ở biên refill và deadline socket Redis cũ. Bài kiểm tra và bằng chứng gốc được giữ nguyên. Các bước nhảy clock và việc dừng gate là quan sát lịch sử, không phải trạng thái hiện tại. |
| 5:00–6:00 | Nêu rằng T09 và phân tích offline T10 đã hoàn tất; giới hạn, oracle Fixed Window `inconclusive`, network counter Redis là tổng traffic, không có resource sampling khi outage, và các điều chưa xác minh vẫn được ghi trong kết quả. Không suy ra HA/production từ prototype mô phỏng. |

Phương án dự phòng ngoại tuyến: [kết quả T10](analysis/T10_RESULTS.md), [bảng T10](worklog/2026-10-20-t10/T10_TABLES.md), [hình đã sinh](worklog/2026-10-20-t10/figures/) và [traceability/checksum](worklog/2026-10-20-t10/README.md). Hình pilot ngày 13/10 và [CSV pilot](worklog/2026-10-13-evaluation/report/runs.csv) chỉ minh họa UI/integration. Không cần internet; nếu Docker lỗi, mở artifact đã lưu.

<a id="truoc-buoi-tap-duot"></a>
## Trước buổi tập dượt

- Mở trước [slides nháp](slides/project3-defense.md), [bảng mixed T10](worklog/2026-10-20-t10/T10_TABLES.md) và [các hình đã lưu](worklog/2026-10-20-t10/figures/); dùng fallback ngoại tuyến, không tái sinh hình.
- Đối chiếu [protocol v1.2](experiments/protocol-v1.2/protocol.md), [manifest v1.2](experiments/protocol-v1.2/manifest.json), [phụ lục v1.3](experiments/protocol-v1.3/protocol.md), [traceability/provenance T10](worklog/2026-10-20-t10/README.md) và [bằng chứng T06](worklog/2026-10-19-atomicity/README.md).
- Khi nêu thống kê, giữ `n=3` và median (min–max); không gọi là confidence interval hay significance. Tách caveat test-source/hash và uncommitted patch của T06 khỏi measurement revision `0291a80fb404fea0eafee8c3431acc3631bb423e`.
- Nêu rõ giới hạn kết luận đã liệt kê ở trên; chưa có rehearsal thực tế, H01 vẫn chờ người học tự xác nhận.

<a id="cau-hoi-tu-kiem-tra"></a>
## Câu hỏi tự kiểm tra

Vì sao local quota có thể bị vượt? FW và TB khác nhau ra sao ở burst? Lua atomicity chứng minh điều gì? 429 khác 503/timeout thế nào? Goodput của client hợp lệ dùng mẫu số nào? Kết quả scaling bị giới hạn thế nào bởi backend mô phỏng? First success khác stable recovery thế nào? Saved-run UI nào chỉ là pilot?

<details>
<summary>Chi tiết setup, restore và evidence T12 (chỉ mở khi cần)</summary>

### Source và phiên bản

Revision nguồn đo T09/T10 là `0291a80fb404fea0eafee8c3431acc3631bb423e`. Revision tích hợp Console/demo đã kiểm tra là `1c3f56dddc12bd405cd3d70ff1b553abda6c787c`, khác revision đo. T10 dùng archive có provenance LFS; không đổi checksum Git/LFS thành hash nội dung archive hoặc ngược lại. Xem [worklog LFS migration](worklog/2026-10-21-lfs-migration/README.md) và [worklog T10](worklog/2026-10-20-t10/README.md).

`git archive` chỉ xuất source snapshot, không phải checkout. Khi cần build/chạy Console, dùng checkout Git thật và kiểm tra HEAD/trạng thái sạch. Console dò `artifacts/console/<id>/status.json` và `request.json`; raw T09 có `p1-*` planned IDs, không thể nạp trực tiếp vào UI mà giữ nguyên ID/metadata. Không đổi ID T09 hay ghi đè archive.

### Saved-run pilot

Ba run pilot ngày 13/10, được lưu trong `artifacts/console/` của bundle V2 và bản đối chiếu `artifacts/t12/saved-pilot-ui-source/artifacts/console/`:

| Mode | Original Console Run ID | Ghi chú |
| --- | --- | --- |
| none | `20261013T022629-bd56e4d4e3a5` | pilot; 720/720; oracle not applicable |
| local | `20261013T022713-1011975d376e` | pilot; clock/fidelity flags được giữ nguyên |
| Redis | `20261013T022742-f79870fc9be7` | pilot; oracle inconclusive |

Ba run được restore vào checkout demo `/tmp/project3-t12-source/artifacts/console/`, bản copy cũng nằm ở `artifacts/t12/saved-pilot-ui-source/artifacts/console/`. Archive gốc SHA-256 `fa3c8eef86e2ef263dbde33fa07e06dfbef5c353e875b03a9ab060abb3ce25be`; 36 file mỗi run khớp per-file hashes trong [manifest](worklog/2026-10-13-console-content/evidence/manifest.json). Pilot source revision `f608873643ed599defe19ede3694338214565318`. Bảng UI chỉ kiểm tra pilot content/integration, không phải kết luận T10.

Bundle V2: `artifacts/t12/PROJECT3-T12-DEMO-PACKAGE-v2.tar.gz`, SHA-256 `d11c6d79d26c8e2d5849e55a9c4c8fbc53a0cc1d4f44b49f333aa10b30c084d0`; gồm saved pilot UI, T10 offline fallback và source snapshot. V1 được giữ nguyên, SHA-256 `4eeb2c3d63e900eec7fc45c7fe46f85fa00dac8d65757d1a6ffd1045b18bbfab`.

Khôi phục vào checkout mới, chỉ khi các thư mục đích chưa tồn tại. Lệnh dừng nếu có thư mục, tránh ghi đè:

```sh
(
set -eu
demo_checkout=$(mktemp -d /tmp/project3-demo.XXXXXX)
GIT_LFS_SKIP_SMUDGE=1 git clone --no-hardlinks --shared . "$demo_checkout"
GIT_LFS_SKIP_SMUDGE=1 git -C "$demo_checkout" checkout --detach 1c3f56dddc12bd405cd3d70ff1b553abda6c787c
test ! -e "$demo_checkout/artifacts/console/20261013T022629-bd56e4d4e3a5"
test ! -e "$demo_checkout/artifacts/console/20261013T022713-1011975d376e"
test ! -e "$demo_checkout/artifacts/console/20261013T022742-f79870fc9be7"
tar -xzf artifacts/t12/PROJECT3-T12-DEMO-PACKAGE-v2.tar.gz -C "$demo_checkout" artifacts/console
cd "$demo_checkout"
go run ./cmd/console
)
```

Lệnh giả định chạy từ repo root có bundle T12, Go/module cache và TCP loopback; giữ repo gốc trong buổi demo vì checkout dùng Git objects chung. Không cần LFS cho pilot saved runs. Chỉ mở saved runs, không bấm **Chạy benchmark**. Với checkout đã có đích, dừng và xác minh hash; không giải nén đè. Worklog [T12](worklog/2026-10-22-t12/README.md) ghi kết quả kiểm tra: extracted IDs, 36 manifest hashes mỗi run, Console build thành công, GET `/api/runs` và artifact listing trả 200, UI đọc artifact; không POST, Docker load, benchmark hay live workload. Dùng V2; không tái tạo package.

### T10 offline fallback và source snapshot

Bản offline nằm trong `artifacts/t12/offline/`; nguồn chuẩn là [T10 results](analysis/T10_RESULTS.md), [bảng](worklog/2026-10-20-t10/T10_TABLES.md), [11 hình](worklog/2026-10-20-t10/figures/) và [traceability/provenance](worklog/2026-10-20-t10/README.md). Các kết luận giữ nguyên giới hạn; FW oracle `inconclusive`. Không tái sinh hình. Nếu cần source snapshot để đóng gói:

```sh
(
set -eu
measurement_export=$(mktemp -d /tmp/project3-measurement-source.XXXXXX)
git archive --format=tar 0291a80fb404fea0eafee8c3431acc3631bb423e | tar -xf - -C "$measurement_export"
printf '%s\n' "$measurement_export"
)
```

Đây chỉ là export revision đo, không có Git metadata; dùng clean checkout riêng để build/start. Có đủ 41 mục gốc trong `SHA256SUMS`; không tái tạo chúng. FW oracle vẫn `inconclusive`.

</details>
