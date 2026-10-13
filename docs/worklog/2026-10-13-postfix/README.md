# Gate sau sửa deadline Redis — 13/10/2026

**Gate thất bại vì clock host; chưa chạy formal.** Chạy đúng [PRESET](PRESET.md) tại revision sạch `cf699bedcc4848f96176954c77c95d1e33b85466` (đã chứa fix Redis `5bf0fe3`), dừng sau hai normal30s vì cùng blocker clock/fidelity. `normal3,mixedRedis1–3` chưa thực hiện; giữ manifest skipped. Không sửa host clock, timeout, tải, runtime hoặc archive cũ.

| Gate | Sent/scheduled | Legitimate success | Errors/fallback | P95lag | Max sent–scheduled/lag residual | Max end–sent/latency residual |
| --- | --- | --- | --- | --- | --- | --- |
| Normal1 | 600/600 | 600 | 0/0 | 1,164ms | 2606,038ms | 2606,037ms |
| Normal2 | 600/600 | 600 | 0/0 | 1,150ms | 2628,761ms | 2628,759ms |

Cả hai0drops/429/backend overload/transport errors, counters mọiAPI/backend và raw/summary reconcile. Nhưng residual vượt ngưỡng5ms đã ghi trước; actual wall-phase legitimate18,267RPS so target20RPS nằm ngoài±5%. Clock discontinuity không được diễn giải thành lag generator2,6s: lag/latency Go dùng monotonic, JSON timestamps mất monotonic. Fix socket deadline đã không phát sinh Redis error trong hai lượt có clock jump này; **không suy thành gate pass** hoặc giải quyết host clock. Oracle FW vẫn `inconclusive`, không correctness pass.

Gate metadata/revision sạch. Sau gate, root bắt đầu thay đổi tài liệu/plotting nên ba Console run đầu có dirty metadata đúng thực tế. Giữ cả ba, không sửa evidence. Root cho phép tạo thêm ba UI integration run từ detached checkout sạch `/tmp/project3-postfix-clean` tại cùng `cf699be`. Mọi load tuần tự và gate kết thúc trước Console; không chạy browser/test đồng thời load.

## Console: kết quả thật và giới hạn so sánh

Cả sáu Console runs: mixed120/20RPS,2API,Q=B20/W1000/r20,backend4/50ms,6s,1repeat. Đây là integration/demo, không thay thế lượt gate hoặc bộ benchmark.

| Checkout/mode | Run ID | Legitimate success /120 | Backend overload | Quality |
| --- | --- | --- | --- | --- |
| Root dirty/none | 20261013T021047-e466d920012b | 56 | 315 | clocks/fidelity đạt, metadata dirty |
| Root dirty/local | 20261013T021113-b665afeb9962 | 87 | 138 | clocks/fidelity đạt, metadata dirty |
| Root dirty/Redis | 20261013T021141-b98223453f84 | 99 | 69 | clocks/fidelity đạt, metadata dirty |
| Clean/none | 20261013T021222-0f331646b42b | 47 | 315 | clock/fidelity thất bại; residual3,201s |
| Clean/local | 20261013T021251-c8b44a0296de | 88 | 130 | clocks/fidelity đạt |
| Clean/Redis | 20261013T021317-49d662965fe1 | 101 | 79 | clock/fidelity thất bại; residual4,189s |

0drops và0limiter errors trong cả sáu. Summary/analysis riêng lượt1 có đủ; mọi counter/trace asserts đạt. Không ghép các outcome trên thành kết luận mode thắng hoặc healthy overhead.

**Real accepted-table validation chưa đạt:** chọn ba clean runs, browser từ chối `Khác cấu hình: images`. `images.json` lưu API/backend manifestIDs khác nhau sau mỗi Compose build dù revision sạch giống nhau; không giả định các image tương đương chỉ từ revision. Đọc chính exactIDs sau tải: RedisAPI1/API2/backend còn tồn tại, giữ RootFS.Layers/Config/Os/Architecture/Variant; none/local sáuID đều `No such image`, giữ lỗi trong `image-inspect.json` từngcase, không thay bằng tag. Do đó chưa có bằng chứng đủ runtime-layer equality để bỏ guard. Không sửa runtime/UI/metadata để ép accepted table.

Browser guard từ chối workload đổi120→121RPS trên **response clone trong test**, cùng raw artifact thật; raw không sửa. Đây là kiểm thử guard khi evidence thay đổi, không phải một lượt tải khác. Desktop1280 và mobile390 không page overflow trong trạng thái refusal; chưa kiểm tra layout bảng accepted vì bảng không xuất hiện. Default-stack polling được dừng trong browser sau measurement để snapshots ổn định; không dựng stack mặc định, không sửa giao diện.

## Evidence, tái kiểm tra và cleanup

[CSV từng lượt](runs.csv),[JSON từng lượt vàphase/class](runs.json) giữ đủ8runs (2gate+6Console),revision/dirty state,max residuals,offered durations/rates/drain,lag,drops,mọiAPIerrors/backend deltas/oracle. [Quality checker](check-quality.py) ghi residual5ms và preset assertions; [gate commands](run-gate.sh) dùng script runner hiện hữu. Rerun cần output mới. Các script helper/HTTP requests/responses/browser checks/skipped manifest/container snapshots được archive nguyên bản.

[Archive](evidence/postfix-artifacts.tar.gz) bỏloadgen binary, giữ paths portable dưới `artifacts/postfix-20261013/`; [SHA256 manifest](evidence/manifest.json) chứa checksum từnginput vàarchive, đã đọc xác nhận từngmember. Original pilot archive không thay đổi. Raw giữ tại `artifacts/postfix-20261013/`; clean source artifacts còn dưới `/tmp/project3-postfix-clean/artifacts/`.

Cả hai Console process đã dừng, project `project3-research-lab` không còn container; trước/sau chỉ unrelated `fast_api_learn_postgres postgres:17`, không đụng tới nó. Không prune/delete unrelated images hoặccontainers; không commit.

Bỏ qua bốn lượt gate sau blocker và formal. Rủi ro: hostclock chưa ổn định; real accepted comparison còn bị imageidentity guard chặn; số liệu Console6s chỉ là integration vàFW inconclusive khôngpass.
