# WSL clock discipline diagnosis (2026-10-19)

## Scope and provenance

Read-only diagnosis on the same WSL machine; no settings, services, host clock, packages, or workloads were changed. Captured at repository revision `60f7dd63cddcc0fcd0889dbe961483634d9a169c`. User reports no manual clock/date adjustment and no custom synchronization tool; this is context, not independent evidence. Full raw batch, observer, status output, and hashes are in `artifacts/clock-discipline-20261019-0312-60f7dd6/`.

The 90-second observer sampled guest realtime, MONOTONIC, MONOTONIC_RAW, BOOTTIME, raw `clock_gettime` syscalls, and `systemd-timesyncd` status once per second. It used a 5 ms realtime-minus-monotonic step threshold. 1,792 clock samples and 91 successful timesync status polls were collected; maximum sample read span was 133.1 microseconds.

## Findings

Three guest realtime steps relative to MONOTONIC were measured: +2.951639 s at 18.288 s, +2.959153 s at 50.796 s, and +2.951175 s at 83.292 s. At the adjacent status polls, `systemd-timesyncd` packet count advanced from 70 to 71, 72, and 73; reported offset was respectively +2.951639 s, +2.959153 s, and +2.951174 s. The daemon was active, using its fallback `ntp.ubuntu.com` source, with a 32-second poll interval. This is a close, repeated correlation between accepted NTP samples and the wall steps, and makes timesyncd a strong candidate contributor. It is not direct proof that timesyncd wrote CLOCK_REALTIME: no clock-setting syscall or kernel writer was traced.

There is an unresolved clock-source anomaly: over the same 90 s MONOTONIC/BOOTTIME advanced about 89.972 s while MONOTONIC_RAW advanced about 98.152 s and realtime about 98.834 s. All three realtime steps also appeared relative to MONOTONIC_RAW (about +2.947 to +2.955 s). BOOTTIME-MONOTONIC differed by only 0.000478 ms, which argues against guest-accounted suspend during this window but does not exclude every VM pause mode. Raw syscall readings closely matched Python clock reads, no `LD_PRELOAD`/`LD_AUDIT` names were set, and no clock-adjusting wrapper was apparent in the targeted mapped libraries. Query-only `adjtimex(mode=0)` returned frequency -33.594 ppm and offset 0 before and after. Time namespace offsets were zero; PID 1 namespace access was denied, so only self namespace was confirmed.

Installed systemd is 255.4. Its installed WSL drop-in says timesyncd is enabled so the WSL clock is synced on host suspend resume. The kernel command line includes `hv_utils.timesync_implicit=1`, and the active clocksource is `tsc`. Microsoft rolling WSL kernel source documents implicit Hyper-V sync only when a sample is at least 5 s ahead of guest realtime, while the observed timesyncd offsets were about 2.95 s; exact running kernel tag source was not verified. This option alone does not establish periodic sync or explain the observed cadence. Because MONOTONIC_RAW itself advanced by the same wall-step amounts and ran substantially faster than MONOTONIC, a direct timesyncd-only explanation is incomplete. The evidence supports timesyncd samples closely coinciding with corrections, while the underlying WSL virtual clock/timebase behavior remains unresolved.

No adjustment event was found or tracing enabled. Default logs may not record each clock adjustment. A direct writer attribution would require a narrowly scoped, read-only observation of clock-setting paths (for example an already available kernel trace facility); configuring ftrace/kprobes would change tracing state and was outside this pass.

## Limits and references

MONOTONIC_RAW and MONOTONIC may share underlying virtual hardware sources and are not independent host-vs-guest clocks. The short window does not establish permanence or a unique actor. Timesyncd correlation is observational and does not demonstrate causation. Hyper-V source reference: [Microsoft WSL kernel `hv_util.c`, rolling 6.18.y branch](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/drivers/hv/hv_util.c); exact running kernel tag was not confirmed. Installed systemd version 255.4; relevant upstream implementation reference: [systemd v255 timesyncd manager](https://github.com/systemd/systemd/blob/v255/src/timesync/timesyncd-manager.c).

## Evidence hashes

Hashes for the raw batch are recorded in `SHA256SUMS` beside this README. The archive contains only this batch's raw samples, observer, preflight output, metadata, summary, and timesync status samples. This README and archive hash are recorded separately in `ARCHIVE-SHA256SUMS` to avoid a circular hash.
