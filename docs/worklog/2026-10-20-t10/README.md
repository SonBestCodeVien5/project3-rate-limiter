# T10 — phân tích offline

T10 chỉ đọc T09 archives, protocol/manifest khóa, ledgers T09 và worklog T06. Không chạy Docker, benchmark, exporter trên các đường dẫn tuyệt đối cũ hay sửa raw evidence.

## Tái lập đầy đủ

Từ root repository, giải nén các archive đã khóa vào thư mục mới:

```sh
mkdir -p /tmp/project3-t10-inputs/{v12,v13,v11}
tar -xzf docs/worklog/2026-10-20-t09-v1.2/T09-V1.2-FORMAL-EVIDENCE.tar.gz -C /tmp/project3-t10-inputs/v12
tar -xzf docs/worklog/2026-10-20-t09-v1.3/T09-V1.3-MISSING-SLOT-EVIDENCE.tar.gz -C /tmp/project3-t10-inputs/v13
tar -xzf /tmp/project3-t10-inputs/v12/project3-t09-v1.2-package/source-raw/previous-v1.1-resume-evidence.tar.gz -C /tmp/project3-t10-inputs/v11
```

Cần Python 3.12 và Matplotlib 3.11.2. Cài trong môi trường cô lập, không thêm dependency vào repo:

```sh
uv venv --python 3.12 /tmp/project3-t10-plot-env
uv pip install --python /tmp/project3-t10-plot-env/bin/python matplotlib==3.11.2
```

Sau đó chạy bằng output path mới:

```sh
MPLCONFIGDIR=/tmp/project3-t10-mplconfig /tmp/project3-t10-plot-env/bin/python scripts/analyze-t10.py \
  --v11-root /tmp/project3-t10-inputs/v11/t09-v1.1-resume-evidence-20261020 \
  --v12-package /tmp/project3-t10-inputs/v12/project3-t09-v1.2-package \
  --v13-package /tmp/project3-t10-inputs/v13/project3-t09-v1.3-package \
  --output /tmp/project3-t10-results
```

Công cụ kiểm tra SHA-256 của archive v1.2/v1.3, archive v1.1 lồng bên trong, checksum indexes, ledgers, exporter, final derived manifest và CSV. Nó nối từng planned run ID với file `analysis.json` đúng hash, rồi xác nhận hash của summary, metadata, Redis sampler log và image artifacts; so sánh giá trị CSV với raw analysis; kiểm tra source revision, runtime và image content. Missing/mismatch thì dừng trước khi xuất kết quả. Đối chứng chỉ bỏ qua field được thay đổi theo protocol: algorithm, state mode, RPS, số API hoặc pause schedule.

Output gồm `run-evidence.csv`, `summary.csv`, `T10_TABLES.md`, `traceability.csv`, `retry-history.json`, `contrast-audit.json`, `aggregates.json`, `provenance.json` và 11 hình ở ba định dạng SVG/PDF/PNG. Tất cả số liên tục là median và min–max trên ba lượt riêng; p50/p95/p99 không được tính từ trace gộp. Goodput mỗi run là `legitimate_successful / elapsed_seconds_including_drain`; hai giá trị này được giữ ở `run-evidence.csv`. `traceability.csv` dùng đường dẫn tương đối trong archive, cùng SHA-256 của raw analysis/summary/network/image files; không phụ thuộc vào `/tmp` cũ. Output path đã tồn tại sẽ bị từ chối.

Đã kiểm tra hai lượt tái tạo trên thư mục output mới; `T10_TABLES.md`, ba CSV, aggregates, retry history, contrast audit và provenance có cùng SHA-256. Đã mở xem PNG preview của biểu đồ latency, scaling và outage; nhãn, mốc API và chú thích median/min–max đều rõ, không bị chồng lấn. `SHA256SUMS` trong worklog bao gồm toàn bộ output bền vững, và được kiểm tra bằng `sha256sum -c`. Hình được vẽ bằng Matplotlib 3.11.2/NumPy 2.5.4 trên Python 3.12.3. Một thư viện dùng kiểm tra PDF (`pdfinfo`) không có trong môi trường; lệnh `file` xác nhận định dạng PDF 1.4 một trang.

## Nguồn và provenance

- Archive v1.2: SHA-256 `ec67b58202c14027ded4f411516dcd5979052d5e384a12ba8f8511a712e06f8d`; checksum index package `be7a09a74d9b51e1b437fae53a31cebbb773dd58ae5d433b9302274751932f6c`.
- Archive v1.3: SHA-256 `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`; checksum index package `d37744967d9fa5527fceda68c26931b03155a08abc3250e24d7f392876c17182`.
- Nested v1.1 archive: SHA-256 `e7122b897a9af2036e09cc178835060cbdaaf9f7c22a7818b5ad6ee8a3fa8ce0`; extracted evidence checksum index `4860855eaca07ff033c2bd0b4607f0da77c1e68fa0538b8587cb84408dfcc292`.
- Locked v1.2 manifest SHA-256 `8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e`; derived final result manifest SHA-256 `d6e74897868bef82750f98cdc0b82025d563ab492c58fa311b5c185fdedcdaf3`; `runs.csv` SHA-256 `f0392733923dc050fc6cf655f47c75e8876051b50e6f21bbf0e34d9b6e715c59`.
- Measurement revision `0291a80fb404fea0eafee8c3431acc3631bb423e`; exporter revision `046654e27e08e2292d554fd96a594226ef86bc7e`, SHA-256 `391c53239e1a4191505f213df30d5924a5c47dec0af15d537c74dd7f2c9106c5`; checker revision `371ed1184800d81791821ab6b048243d6510fbcb`.
- T06 atomicity evidence: [README](../2026-10-19-atomicity/README.md) and its artifact checksums.

Kết quả narrative: [T10_RESULTS.md](../../analysis/T10_RESULTS.md). Các bảng được sinh từ dữ liệu archive; không chỉnh tay để tạo số liệu. T10 không mở lại phép đo hoặc thay đổi protocol.
