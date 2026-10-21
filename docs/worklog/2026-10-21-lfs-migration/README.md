# LFS migration lịch sử chưa push — 2026-10-21

Đã chuyển đúng ba archive vượt giới hạn file GitHub sang Git LFS trong 33 commit của `main` chưa có trên `origin/main`. `origin/main` tại thời điểm chuyển là `10a7a404817b95689c7e549a2b2ac60bf246aa79`; `main` gốc là `d04344147148fe0d687bd0a1fe4d6c617deaf05c`, sau chuyển là `43e4de94e257a5b9588902596d8d4ec22daa852f`. Các commit đã push giữ nguyên. Bảng ánh xạ đầy đủ SHA commit cũ → mới nằm trong [commit-map.csv](commit-map.csv) (33 dòng, do `git lfs migrate import --object-map` tạo).

| Archive | Commit gốc thêm file | Kích thước | SHA-256 gốc và LFS OID |
| --- | --- | ---: | --- |
| `docs/worklog/2026-10-20-t09-formal/T09-FORMAL-PARTIAL-EVIDENCE.tar.gz` | `627f7ff2ede3fe98bc87abd992e42eab38ab77ad` | 132093287 bytes | `20f8d21845b8f381561ad293aef5b326d6bc85d63c39436e25ca9906a7e0a505` |
| `docs/worklog/2026-10-20-t09-resume/T09-V1.1-RESUME-EVIDENCE.tar.gz` | `9778b03761d1b35e2173fadcd1c84061bbade780` | 394853956 bytes | `e7122b897a9af2036e09cc178835060cbdaaf9f7c22a7818b5ad6ee8a3fa8ce0` |
| `docs/worklog/2026-10-20-t09-v1.2/T09-V1.2-FORMAL-EVIDENCE.tar.gz` | `6f266496f011f95c29063ba66d8db1855e781000` | 583519788 bytes | `ec67b58202c14027ded4f411516dcd5979052d5e384a12ba8f8511a712e06f8d` |

Các byte archive trong working tree đã được khôi phục từ LFS object cache và SHA-256 khớp bản gốc. `git lfs fsck --objects HEAD` thành công. Commit nguồn T10 `0291a80fb404fea0eafee8c3431acc3631bb423e` vẫn nguyên vẹn và là ancestor của `main` mới; protocol, manifest, báo cáo cũ và checksums không bị sửa.

Bản sao lịch sử gốc nằm tại ref local `refs/archive/pre-lfs/d043441` và bundle đã xác minh `artifacts/pre-lfs-migration/original-history-d043441.bundle` (SHA-256 `2266f4700b8d85e47c55f77b069de0b814ad9005a388a35664318cb140cfc41f`). Bundle được giữ trong thư mục bị ignore. Ref backup không được push. Remote chưa được cập nhật tại thời điểm ghi mục này.

Ba file tổng cộng 1110467031 bytes (1.03 GiB). Tài liệu GitHub hiện nêu giới hạn 2 GB cho mỗi file trên Free/Pro và quota kèm theo 10 GiB dung lượng/bandwidth; mức dùng hiện tại của tài khoản không đọc được ở đây. Việc upload sẽ kiểm tra quyền truy cập và quota hiện có; không thay đổi billing. Tham khảo [git-lfs-migrate](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc), [giới hạn Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage) và [quota Git LFS](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).
