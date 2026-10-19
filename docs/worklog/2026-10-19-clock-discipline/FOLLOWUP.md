# Tick-rate follow-up (read-only; 2026-10-19)

This is an addendum to v1; it preserves the original README, archive, raw samples, and hashes unchanged. The new query and analysis are from the same captured observation at revision `60f7dd63cddcc0fcd0889dbe961483634d9a169c`; no new live observation or clock/service setting change was performed.

## Direct rate parameter evidence

`adjtimex(modes=0)` reported `tick_us=9167` both before and after the 90-second observation, with frequency `-33.5937805 ppm`; a separately compiled C helper using the installed glibc `<sys/timex.h>` and the same read-only mode reproduced the values. Runtime `sysconf(_SC_CLK_TCK)` (`getconf CLK_TCK`) is 100. The running kernel has `CONFIG_HZ=250`; this is the scheduler tick configuration and must not be confused with USER_HZ. The installed running-kernel header sets `__USER_HZ` to 100. Linux UAPI defines `timex.tick` as microseconds per tick and `ADJ_TICK` as its setter; kernel timekeeping source describes `tick_usec` as a USER_HZ period. At USER_HZ=100 the nominal tick is 10,000 µs, making 9,167 µs a nonstandard value.

Across the existing samples, MONOTONIC advanced 89.972190856 s while MONOTONIC_RAW advanced 98.151508971 s. MONOTONIC/RAW = 0.9166664048; six local segments each measured 0.91666638–0.91666645. The simple rate estimate `(9167 / 10000) × (1 − 33.5937805 ppm)` is 0.9166692046, predicting 89.972465657 s of MONOTONIC over the observed RAW duration, only 0.275 ms from the measurement. This strongly supports the nonstandard tick as the rate parameter explaining the continuous MONOTONIC/RAW divergence in this window. It does not prove who set that value or whether the value is persistent across restarts.

Correction to the v1 wording: MONOTONIC_RAW did **not** jump at the three realtime step events. Its measured rate relative to MONOTONIC was smooth and nearly identical on both sides of each event (RAW/MONOTONIC about 1.0909093–1.0909097). The discrete realtime advances of about 2.95 s happened relative to both clocks. The reported timesyncd packet offsets matched those advances; installed systemd is 255.4, and v255 source uses `ADJ_SETOFFSET` for offsets >=0.4 s but does not use `ADJ_TICK`. Thus timesyncd corrections are a plausible response to the rate mismatch, while the process that installed tick=9167 remains unknown.

The rolling WSL kernel source initializes `tick_usec` from `USER_TICK_USEC` and changes it when an `ADJ_TICK` mode is supplied. The installed kernel headers identify the running build as 6.18.54.1, but no matching local full kernel source was available to verify the WSL implementation at that exact tag. The `auditctl` and `ausearch` utilities are absent, so existing `AUDIT_NTP_TICK` records could not be queried; audit was not enabled or changed. No syscall tracing was configured.

## Concrete reversible proposal (not performed)

If a later approved controlled test is warranted, and USER_HZ=100 is re-confirmed at test time, the minimal candidate change is a temporary `adjtimex` call with only `modes=ADJ_TICK` and `tick=10000` µs. It would leave frequency and NTP service configuration untouched, but requires `CAP_SYS_TIME` and changes the system timebase used by all processes. Capture the query-only `tick` and frequency immediately before the test. To rollback, issue only `modes=ADJ_TICK, tick=9167`, then query again and verify tick=9167; the separate frequency field should remain whatever timesyncd has currently disciplined. A maximum ~40-second bounded comparison would distinguish the rate mechanism and allow at most one 32-second timesyncd poll. Do not do this during deadline-sensitive workloads. This proposal is not a proven fix and has not been executed.

## References

- Linux `timex.tick` and `ADJ_TICK`: [UAPI header](https://github.com/torvalds/linux/blob/master/include/uapi/linux/timex.h).
- Kernel USER_HZ timekeeping parameter: [Linux `kernel/time/ntp.c`](https://github.com/torvalds/linux/blob/master/kernel/time/ntp.c).
- WSL rolling branch use of `tick_usec` and `ADJ_TICK`: [Microsoft WSL kernel `kernel/time/ntp.c`](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/kernel/time/ntp.c) (running tag not directly confirmed).
- `CLOCK_MONOTONIC_RAW` and timekeeping: [Linux `kernel/time/timekeeping.c`](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/kernel/time/timekeeping.c).
- Exact installed systemd major version path: [systemd v255 timesyncd manager](https://github.com/systemd/systemd/blob/v255/src/timesync/timesyncd-manager.c).
- USER_HZ vs kernel HZ distinction and `adjtimex` permissions: [Linux `time(7)`](https://man7.org/linux/man-pages/man7/time.7.html), [Linux `adjtimex(2)`](https://man7.org/linux/man-pages/man2/adjtimex.2.html).
