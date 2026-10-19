# Trace layout preflight (2026-10-19)

The native Ubuntu WSL kernel reports `6.18.54.1-microsoft-standard-WSL2` on x86_64, with GCC 13.3.0 available. A directory named `/usr/src/linux-headers-6.18.54.1-microsoft-standard-WSL2` exists and the module build symlink resolves there, but the expected exact-release UAPI header `include/uapi/linux/timex.h` is missing. The directory also lacks the checked build identity files (`Makefile`, generated `utsrelease.h`, `kernel.release`) and checked x86 UAPI header. Its internal `include/linux/timex.h` contains a `struct __kernel_timex` declaration but has no `dpkg-query` owner; the paired `include/linux/timekeeping.h` is absent. No `do_adjtimex` prototype was found in the targeted headers checked.

The generic `/usr/include/linux/timex.h` also defines `struct __kernel_timex`, but it cannot establish the running WSL kernel's exact layout. The prepared C `offsetof` query was not compiled. No offsets or sizes are claimed, and no guessed or generic-header layout was used. This blocks the numeric-fetch trace fallback. No tracing was configured and no clock/service setting was changed.

Detailed outputs and probe source are in `evidence.tar.gz`, with its digest in `ARCHIVE-SHA256SUMS`. No further header/source alternatives were searched after the exact release tree failed verification.
