# Temporary tick trial (2026-10-19)

## Result

One bounded native-WSL trial was executed after the sandbox process was denied `ADJ_TICK` with `EPERM`. The sandbox attempt did not change the tick and produced no samples; its exact partial evidence remains under `artifacts/tick-trial-20261019-0417-dd307a6/attempt-sandbox-eperm/`.

In the same current Ubuntu WSL distro, the precondition query confirmed `USER_HZ=100`, `tick_us=9167`, and `freq_scaled_ppm=-2201602` (`-33.593780518 ppm`). A detached 37-RAW-second watchdog was started before the setter. The narrowly scoped setter changed tick 9167→10000 and immediately queried back `tick_us=10000`, with return state 0 and no frequency change. The main helper sampled 651 realtime/monotonic/raw/boottime records and 36 read-only timesync status records over 34.960484 RAW seconds.

The sample slopes indicate that the 10000-tick rate persisted for only about the first 6.9 RAW seconds: median MONOTONIC/RAW was 0.999966422 from 0–6.7 seconds, then 0.916666411 over 7–10 seconds and 0.916666421 over the final 5.3 seconds. A mixed interval at 6.884–6.938 RAW seconds contains the transition. The pre-restore query then found `tick_us=9167`, before our rollback path would have issued a setter. We therefore infer that another actor or kernel path rewrote the tick during the observation; the exact time, writer, and mechanism are not identified. The overall 0.933085680 ratio is a mixed-parameter result and is not a valid full-window rate for tick=10000.

The only wall step over 5 ms was +2332.935 ms at about 34.796 RAW seconds. Timesyncd status packet count advanced 102→103 at about 35.012 RAW seconds and reported offset +2.332935 s (prior offset +2.935564 s); this is consistent with a wall correction correlated with an NTP update but does not identify the source of the earlier tick rewrite. Tick was already 9167 at the pre-restore query, so the helper's restore command did not write it. The subsequent query verified `tick_us=9167` and unchanged frequency. The watchdog exited successfully after the main path disarmed it; its PID was absent at cleanup. A final native read-only query again confirmed tick=9167.

A point-in-time, read-only snapshot found several processes holding `CAP_SYS_TIME`, including systemd-timesyncd, systemd/init components, cron, unattended-upgrades, containerd, dockerd, and session processes. Capability ownership only identifies candidates; it does not establish which process reset the tick. No tracing/audit setup, second trial, service change, or further clock mutation was performed. The temporary trial is incomplete for its intended comparison because the requested tick was not held for the full active interval. It does not authorize or establish a permanent change.

## Provenance and limits

Revision: `dd307a6a5775cb122ffa207ec5591de8d134a569`. The worktree was clean at launch. The user authorized one temporary 9167→10000 µs `ADJ_TICK` trial, bounded by a RAW-clock watchdog, followed by restoration and verification. USER_HZ and original tick matched the required preconditions. The execution occurred in the exact current Ubuntu WSL distro through the native `wsl.exe` route; no UAC/admin settings or system services were changed.

The setter's immediate readback proves tick=10000 at that point. There is no timex query at the observed rate transition, so the exact rewrite timing and actor remain inferred. The final value 9167 and frequency match the original values. The paired wall/time-sync evidence does not attribute either the tick rewrite or wall adjustment. The capabilities snapshot is post-trial and cannot establish historical ownership.

## Evidence

Raw samples, scoped C helper and Python orchestration, pre/post queries, watchdog state, sandbox EPERM attempt, analysis, process capability snapshot, and checksums are included in `evidence.tar.gz`. `ARCHIVE-SHA256SUMS` records the archive digest. Raw artifact directories are retained separately. No unrelated logs or process arguments/environment were collected.
