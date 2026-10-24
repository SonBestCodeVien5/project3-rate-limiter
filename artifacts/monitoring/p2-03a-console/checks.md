# P2-03A — triển khai có, acceptance chưa đạt

Phiên 24/10/2026 chỉ làm P2-03A. Người dùng cấp G1/G2 và **đúng một attempt G3** qua nút Console **Chạy benchmark**; không có `/work` probe/setup workload, retry, outage, P2-04+, T09/T10 hoặc push.

## Kết quả

- **G1:** opt-in trên Console → `research-pilot.sh` → loadgen hiện có; giữ opt-out/JSON `/metrics`, topology 1/2/4, lock/cancel/scoped cleanup. File_sd chỉ API/backend; aliases `console-*` và `fixed-*` tách DNS; monitoring sở hữu scrape network. UID dashboard `project3-monitoring-demo`, folder `project3-monitoring-folder`, datasource `project3-prometheus` giữ nguyên.
- **G2:** `promtool` xác nhận syntax; cảnh báo chưa có `*.json` là đúng khi chưa đăng ký run. Fixed targets UP; list/folder mở đúng dashboard; 7 panel render, 11 biểu thức query có dữ liệu, không lỗi query/JavaScript hoặc No data. JSON `/metrics` vẫn 17 fields ở cả ba service; final counters `/work` đều 0. Sau sửa permissions, manifest thực tế có mode `0644` và Prometheus đọc được; file thử `.permission-check` không khớp glob file_sd, đã gỡ đúng owner.
- **G3: thất bại, không retry.** UI đã submit 1 lần, HTTP 201, run `20261024T145701-272e462e6502`. Effective request/policy/topology đúng custom normal, toàn bộ legitimate, Redis/FW/fail-closed, 2 API, Q20/1s, backend 4/50ms, 20 RPS/30s/1 repeat. Source `5862b90087f3e684a1ece7907fe2ba67d482d3a9` (xem hash đầy đủ trong `case/git-revision.txt`), working tree sạch.
- Runner dựng case healthy/lấy before metrics và ghi image identities, rồi không tạo được file manifest vì thư mục thuộc UID `65534`, khác runner UID `1000`. Record `incomplete`; runner cleanup research containers/network. **Loadgen chưa start**, không có summary/trace/sent/drops. Không ghi generator drops = 0. Không có samples API/backend research, UTC load/drain/final-scrape bounds hoặc Grafana link cho case hoàn tất.
- Vì thiếu dữ liệu tải, **Console→Grafana acceptance, research queries/panels và timing 1s scrape/1s file_sd/4s lookback-rate vẫn chưa được xác minh**. P2-06 coverage pending; không tính thành case thành công hoặc cấp thêm attempt.

## Source, kiểm tra và sửa lỗi

| Revision | Kết quả |
| --- | --- |
| `18f4e287` | Luna triển khai opt-in; Console Go tests, UI JS 6/6, topology 4, lifecycle mock 5, shell/static/Compose/link checks đạt. Go cache mặc định không ghi được, cache `/tmp` pass. Mock HTTP listener ban đầu bị sandbox chặn; tests chuyển mock query trong process. |
| `5862b90` | Luna sửa alias isolation, strict post-drain scrape, recheck sau lookback, registration sau healthy/baselines, manifest atomic/ownership; lifecycle 8 và topology 4 đạt. Đây là source attempt. |
| `b4b3f3c` | Sau attempt thất bại: Luna sửa manifest `0644`, preflight owner/quyền trước research resources và runbook; lifecycle 9/9 đạt, shell/compile/whitespace đạt. Không retry. |
| `30fb223` | Luna phục hồi fixed API/backend trên default network, alias `fixed-*`; static merged Compose/topology 5/5 đạt. G2 root recreate đúng bốn service fixed; cuối cùng cả 7 service healthy. |

Root không lặp lại focused code suite do worker đã chạy; root thực hiện runtime integration sau khi Playwright MCP không phản hồi. Browser local dùng bản Playwright/Chromium đã cài, không thêm dependency hay workflow load mới. Các script `*.cjs` trong evidence chỉ ghi thao tác browser/check của phiên, không phải runner benchmark thay thế. Hai lần login selector ban đầu timeout trước submit; đã sửa bước chờ hydration và login thành công.

Registration failure đã bộc lộ lỗ hổng G2 setup và mode `0600` của NamedTemporaryFile; cả hai đã sửa sau attempt. Một regression trung gian đưa fixed API/backend ra khỏi default network gây Nginx health 502; final fix/recreate khôi phục network và health. Lệnh Nginx reload trung gian thất bại do không resolve API; giữ log, không coi là pass.

## UTC và artifacts

`outcome.json` là bản tóm tắt máy đọc được; `case/` giữ request/status, source/dirty state, policy/effective Compose, image IDs/digests đã lọc, before metrics, registration record và lỗi runner. `g3-ui-request.json` xác nhận cấu hình thực từ UI; `g3-timeline.json` ghi target-state trong attempt. `final-console-source-query.json` trả result rỗng. Không dựng khoảng load giả từ thời điểm submit.

- UI submit: `2026-10-24T14:57:01.783553281Z`.
- Registration record: `2026-10-24T14:57:23.430Z`; deregistration/incomplete `2026-10-24T14:57:23.553Z`.
- Run kết thúc sau cleanup: `2026-10-24T14:57:26.260650641Z`.
- Load/drain/final scrape: **không xảy ra/không có dữ liệu**. Pre-load lookback chưa bắt đầu.
- Final config/source/dirty state và runtime UTC ở `final-runtime-state.json`; G2 permission check ở `g2-permission-verification.json`. Source dirty ở G2 cuối chỉ gồm cập nhật tài liệu đang chốt, không diễn giải thành source attempt.

Ảnh `grafana-list.png`, `grafana-folder.png`, `fixed-panels-*.png` chứng minh regression fixed; `g3-console-config.png` và `g3-console-result.png` chứng minh form/kết quả attempt thất bại. Không dùng ảnh fixed thay bằng chứng research. New telemetry giữ riêng T09/T10; không đo overhead hoặc suy latency/goodput/correctness từ counters.

## Credentials và giới hạn

Công cụ MCP `browser_fill_form` đã echo credential trong tool result lúc login. Không lặp lại trong evidence/Git và không tự đổi mật khẩu đã có. Quét exact bytes của password trên evidence/diff không thấy match; cần đổi mật khẩu riêng sau phiên. Browser auth state tạm ở `/tmp`, không commit; file MCP gốc được giữ trong ignored `artifacts/monitoring/p2-03a-console-private/mcp/`, không thuộc manifest evidence.

Không thực hiện live cancellation/kill/stale recovery bằng một run khác; chỉ focused mocks. Không có load samples để xác nhận post-drain behavior, UTC clock accuracy hoặc sample density. Không chạy full code suite, nghiên cứu hoặc learning confirmation. `SHA256SUMS` chỉ bao phủ các file đã chọn trong `evidence-files.json`; raw ignored artifacts và lịch sử giữ nguyên.

## Lifecycle và prerequisite

Research resources đã được cleanup bởi runner hiện hữu: không còn container thuộc `project3-research-lab`, không còn `active.json`. Giữ stack `project3-monitoring-demo` gồm Redis/backend/2 API/Nginx/Prometheus/Grafana, hai named volumes và monitoring networks; 7 service healthy, 3 fixed targets UP. Console do phiên này tạo vẫn ở `127.0.0.1:8090`. Grafana `127.0.0.1:13000`, Prometheus `127.0.0.1:19090`.

Dừng Console bằng lệnh trong `console-stop-command.txt` (SIGTERM process group do phiên tạo); controller giữ cleanup owner. Dừng monitoring từ repo root, giữ volumes:

```bash
GRAFANA_ADMIN_PASSWORD_FILE="$PWD/.secrets/grafana_admin_password" \
  docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml down
```

Không `down -v`, prune, FLUSHDB, xóa named volume/ignored evidence hoặc điều khiển project khác. **Dừng tại P2-03A chưa đạt acceptance. Prerequisite chính xác: người dùng cấp scope G3 mới cho một attempt qua Console với code đã sửa; chưa chuyển P2-04 hoặc tự retry.**
