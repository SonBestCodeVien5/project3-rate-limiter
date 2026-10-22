# Gói demo/source T12

**Trạng thái (22/10/2026):** T09 đã hoàn tất; T10 đã phân tích offline; T11 đã tích hợp báo cáo. Gói này chuẩn bị source snapshot, saved-run UI pilot và offline fallback cho demo. Nó không cấp quyền chạy workload. Theo dõi task tại [REMAINING_WORK_PLAN.md](REMAINING_WORK_PLAN.md), giới hạn đo tại [PROTOCOL_READINESS.md](experiments/PROTOCOL_READINESS.md), và cách trình bày tại [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Source và phiên bản

- Revision nguồn đo T09/T10: `0291a80fb404fea0eafee8c3431acc3631bb423e`.
- Revision tích hợp Console/demo đã kiểm tra: `1c3f56dddc12bd405cd3d70ff1b553abda6c787c`. Đây là revision riêng, không phải revision đo.
- T10 dùng archive có provenance LFS; không đổi checksum Git/LFS thành hash nội dung archive hoặc ngược lại. Xem [worklog LFS migration](worklog/2026-10-21-lfs-migration/README.md) và [worklog T10](worklog/2026-10-20-t10/README.md).
- Bản xuất `git archive` chỉ là source snapshot, không phải Git checkout. Khi cần build/chạy để thử demo, dùng checkout thật tại `/tmp/project3-t12-source` nếu còn tồn tại; kiểm tra HEAD và trạng thái sạch trước khi dùng.

## Saved UI và giới hạn restore

Console dò `artifacts/console/<id>/status.json` và `request.json`; các file này là envelope metadata của ứng dụng. Raw T09 evidence theo schema protocol và có `p1-*` planned IDs, vì vậy không thể được nạp trực tiếp vào UI mà giữ nguyên IDs/metadata. Đừng đổi IDs T09 thành Console IDs hoặc viết đè archive để làm chúng tương thích.

Để trình bày bảng saved-run đã kiểm tra, dùng bộ ba pilot Console ngày 13/10 với đúng original IDs. Bundle V2 lưu ba thư mục dưới `artifacts/console/`; bản copy đối chiếu nằm ở `artifacts/t12/saved-pilot-ui-source/artifacts/console/`:

| Mode | Original Console Run ID | Ghi chú |
| --- | --- | --- |
| none | `20261013T022629-bd56e4d4e3a5` | pilot; 720/720; oracle not applicable |
| local | `20261013T022713-1011975d376e` | pilot; clock/fidelity flags được giữ nguyên |
| Redis | `20261013T022742-f79870fc9be7` | pilot; oracle inconclusive |

Ba run gốc đã được restore vào demo checkout riêng `/tmp/project3-t12-source/artifacts/console/` và được đóng gói ở `artifacts/t12/saved-pilot-ui-source/artifacts/console/`. Archive nguồn có SHA-256 `fa3c8eef86e2ef263dbde33fa07e06dfbef5c353e875b03a9ab060abb3ce25be`; 36 file mỗi run khớp per-file hashes trong [manifest](worklog/2026-10-13-console-content/evidence/manifest.json). Source revision các lượt pilot là `f608873643ed599defe19ede3694338214565318`; bản Console hiện tại là revision riêng. Giữ archive gốc nguyên vẹn. Bảng Console là bằng chứng UI/content cho pilot, không phải bảng kết luận T10.

Khôi phục vào checkout demo mới chỉ khi ba đích chưa tồn tại; lệnh dừng nếu đã có thư mục để tránh ghi đè:

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

Lệnh trên giả định đang chạy từ repo root có bundle T12, Go/module cache sẵn dùng và TCP loopback được phép. Checkout dùng Git objects chung với repo gốc; giữ repo gốc trong suốt buổi demo. Các archive LFS không cần cho bước xem pilot nên bỏ smudge ở đây. Console có nút chạy benchmark; chỉ mở saved runs trong buổi trình bày. Với checkout đã có thư mục đích, dừng và xác minh hash; đừng giải nén đè lên. Đây là hướng dẫn khôi phục; kết quả kiểm tra T12 dùng checkout riêng được ghi tại worklog.

T10 offline fallback được bundle trong `artifacts/t12/offline/` và có bản gốc ở [T10_RESULTS.md](analysis/T10_RESULTS.md), [bảng](worklog/2026-10-20-t10/T10_TABLES.md), [11 hình](worklog/2026-10-20-t10/figures/) và [traceability/provenance](worklog/2026-10-20-t10/README.md). Các kết luận bị giới hạn theo tài liệu; Fixed Window oracle vẫn `inconclusive`. Mở các file này nếu Docker không chạy hoặc cần trình bày kết quả chính thức.

## Tạo source snapshot và thử build

Trong repository có đủ object Git/LFS:

```sh
(
set -eu
measurement_export=$(mktemp -d /tmp/project3-measurement-source.XXXXXX)
git archive --format=tar 0291a80fb404fea0eafee8c3431acc3631bb423e | tar -xf - -C "$measurement_export"
printf '%s\n' "$measurement_export"
)
```

`git archive` export chỉ dùng để đóng gói source revision đo; clean checkout có metadata Git được dùng cho thử build/start Console. Nếu checkout snapshot T12 chưa có, tạo source checkout từ revision tích hợp đang muốn đóng gói thay vì gọi export là checkout. Build/start Console chỉ bind loopback. Demo saved runs không cần bắt đầu một lượt chạy. Không dùng các nút **Bắt đầu benchmark** hoặc request mẫu nếu mục tiêu chỉ là trình bày saved evidence.

## Artifact T12

Worklog [2026-10-22-t12](worklog/2026-10-22-t12/README.md) ghi source revisions, checkout/process, saved IDs, checksum package và các kiểm tra/giới hạn. Bản package đầu được giữ nguyên; bản hoàn chỉnh V2 gồm pilot UI, T10 offline fallback và source snapshot tại `artifacts/t12/PROJECT3-T12-DEMO-PACKAGE-v2.tar.gz`.
