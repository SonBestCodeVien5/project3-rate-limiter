# Bounded ADJ_TICK writer-trace attempt (2026-10-19)

At revision `02dca6c8ca317e40782d3f81ced69f7cd98fc081`, a single bounded native Ubuntu WSL trace setup was attempted to identify calls requesting `ADJ_TICK` without issuing any clock setter. The intended unique kprobe was at `do_adjtimex` entry with BTF-typed `modes` and `tick` fields, filtered to `modes & 16384`, in a new tracefs instance with a 64 KB buffer and a maximum 45 RAW-second capture. No capture occurred.

The first helper invocation stopped before registering a probe because it checked for instance event controls too early; cleanup removed the empty instance. After correcting the order, the typed kprobe registration write returned `EINVAL` (`OSError: [Errno 22] Invalid argument`). No generated event format was available. This is a registration/typed-fetch failure; the precise parser subreason cannot be distinguished from the available error. In keeping with the stop rule, no guessed offsets, alternate probes, or retries were used.

Cleanup removed the unique trace instance and confirmed that the unique probe was absent. The event was never enabled. Global tracefs values remained `tracing_on=1` and `current_tracer=nop`. Read-only `adjtimex(modes=0)` queries before and after setup reported tick=9167 µs and frequency=-2201602 scaled ppm (-33.593780518 ppm). No clock, tick, frequency, NTP or service setting was changed. Both calls were synchronous; no background process remains from the attempt. Event count and trace duration are zero, so this attempt does not identify the writer.

The bounded outputs, helper source, both setup results, and cleanup notes are in `evidence.tar.gz`; the archive digest is in `ARCHIVE-SHA256SUMS`. The trace design was informed by the kernel kprobe and ftrace documentation and the Microsoft WSL rolling `linux-msft-wsl-6.18.y` source; the running WSL kernel identifies as 6.18.54.1, so source details are not exact-build verification:

- [Kernel kprobe tracing documentation](https://docs.kernel.org/trace/kprobetrace.html)
- [Kernel ftrace documentation](https://docs.kernel.org/trace/ftrace.html)
- [Microsoft WSL `timekeeping.c`](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/kernel/time/timekeeping.c)
- [Microsoft WSL `ntp.c`](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/kernel/time/ntp.c)
- [Microsoft WSL `posix-timers.c`](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.18.y/kernel/time/posix-timers.c)
