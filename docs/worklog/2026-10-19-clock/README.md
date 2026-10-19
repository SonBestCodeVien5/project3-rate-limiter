# Read-only clock observation — 2026-10-19

A fresh 90-second observer run on revision `32194714c979a03cdeee6ac0b88953481cbcd0d6` sampled `CLOCK_REALTIME` and `CLOCK_MONOTONIC` at about 20 Hz using the 2026-10-13 archival algorithm. It recorded 1796 samples over 90.037 monotonic seconds. The wall span was 98.877 seconds. Three adjacent-sample real-minus-monotonic deltas exceeded the unchanged 5 ms threshold: +2961.301 ms, +2947.073 ms, +2931.132 ms. Maximum read span was 90.565 µs.

The result fails the T01 observation gate: steps recurred, so do not proceed to T03 or any benchmark run in this environment. This observation does not establish whether the clock will always step or identify the actor. Host metadata reports WSL2 (`systemd-detect-virt`: `wsl`), kernel `6.18.54.1-microsoft-standard-WSL2`, and current clocksource `tsc`. `timedatectl` was inaccessible because the system bus returned `Operation not permitted`; available read-only adjustment-service diagnostics and their outcomes are preserved in `environment.json`. No clock, NTP, clocksource, or Docker service settings were changed; no benchmark or load ran.

**Next prerequisite:** use a measurement environment that passes the same independent observation, or provide read-only access to the Windows host/hypervisor time-adjustment diagnostics needed to identify the source. Do not alter system time settings until the adjustment source and permitted scope are known. T02 portability work is independent and may continue.

Evidence is in [`clock-20261019-0248-32194714/`](../../../artifacts/clock-20261019-0248-32194714/): observer script (only the archival hardcoded output path changed), raw `samples.jsonl`, `summary.json`, host `environment.json`, process stdout/stderr, and SHA-256 manifest. Repository state at capture: `32194714c979a03cdeee6ac0b88953481cbcd0d6`; worktree status captured in `environment.json`.

## Windows host diagnostics access attempt

On 2026-10-19 at 02:51 UTC, the WSL-visible `w32tm.exe` and `powershell.exe` paths existed. `w32tm /query /status /verbose`, `w32tm /query /configuration`, and a PowerShell query restricted to System events from `Microsoft-Windows-Kernel-General` / `Microsoft-Windows-Time-Service`, IDs 1, 35, 37, and 50, between 02:40–03:00 UTC were each attempted read-only with a 20-second timeout. Each exited 1 immediately with `<3>WSL (...) ERROR: UtilBindVsockAnyPort:317: socket failed 1`; no Windows command output was obtained. This records an interop execution restriction, not a clock or service result. Exact captured output is in `windows-host-diagnostics.txt`.

**Windows-side handoff:** in a local PowerShell session, run these read-only queries and share their output (redacting machine/domain identifiers if desired):

```powershell
Get-Service W32Time | Select-Object Name, Status, StartType
w32tm /query /status /verbose
w32tm /query /configuration
$start = [datetime]::Parse('2026-10-19T02:40:00Z').ToUniversalTime()
$end = [datetime]::Parse('2026-10-19T03:00:00Z').ToUniversalTime()
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start; EndTime=$end; Id=@(1,35,37,50); ProviderName=@('Microsoft-Windows-Kernel-General','Microsoft-Windows-Time-Service')} | Select-Object TimeCreated, Id, ProviderName, Message
```

These diagnostics may help identify an adjustment actor; until output supports attribution, the source remains unknown. A separate measurement environment that passes the independent observer is also a valid next prerequisite.

## Bounded Windows retry through approved sandbox access

A single sandbox-escalated, read-only retry reached Windows without Windows admin/UAC elevation. `w32tm /query /status /verbose` returned `The service has not been started. (0x80070426)`; `/query /configuration` returned the same. The targeted System event query for the already specified 02:40–03:00 UTC window and time-related providers/IDs ran successfully but found no matching events. This supports only that W32Time was not started at query time and that no matching events were available in that filtered interval; it does not attribute the discontinuities or rule out other adjustment actors. Exact commands and outputs are in `windows-escalated-retry.txt`.

The next exact prerequisite remains either a different measurement host that passes the observer or user-provided relevant Windows/hypervisor time-adjustment evidence (the local read-only query found no matching records and W32Time was stopped). Do not infer that starting or changing W32Time is the correct remedy.

## Paired Windows / WSL observation — 2026-10-19

At fixed revision `a533a8062932b4f32f8a3318eaea13cbc05c170f`, two read-only 90-second observers ran concurrently: Windows `DateTimeOffset.UtcNow` vs high-resolution `Stopwatch`, and WSL `CLOCK_REALTIME` vs `CLOCK_MONOTONIC` plus `CLOCK_BOOTTIME`. The WSL sample interval was 50 ms; the step threshold remained 5 ms. Windows captured 1,433 samples over 89.808 seconds between first/last samples, with no adjacent residual above 5 ms and +2.612 ms total wall-minus-Stopwatch residual. WSL captured 1,795 samples over 90.048 monotonic/boottime seconds; realtime advanced 98.914 seconds (+8.866 seconds relative to monotonic). Three forward realtime steps recurred at elapsed monotonic times 24.64, 57.11, and 89.60 seconds, with residuals +2.955, +2.951, and +2.960 seconds. `CLOCK_BOOTTIME` minus `CLOCK_MONOTONIC` span differed by only +0.0027 ms. This does not show a Windows wall-clock step while the WSL steps recurred. The boottime result argues against a guest-accounted suspend interval during this window; it does not rule out every virtual-machine pause mode.

A bounded read-only WSL time-source status/log query immediately after the run found `systemd-timesyncd` active and `NTP=yes`, `NTPSynchronized=yes`; `chrony`/`ntpd` units were absent. No matching time-daemon journal entries or filtered `hv_utils`/time-sync kernel journal lines were available for the approximate sample interval. `/proc/cmdline` includes `hv_utils.timesync_implicit=1`. This makes guest time-discipline paths plausible, but the service state was sampled after the run and no event log identified the writer. **Supported diagnosis:** the discontinuous clock observed here is WSL `CLOCK_REALTIME` relative to WSL monotonic/boottime, while Windows UTC remained smooth relative to Windows Stopwatch in the paired window. The exact actor remains unknown; systemd-timesyncd, WSL/Hyper-V guest synchronization, or another guest-side mechanism have not been distinguished. WSL and Windows monotonic clocks may share a virtualized counter base, so this is localization, not independent hardware calibration. One window cannot establish permanent stability.

The measurement and diagnostic outputs, scripts, environment, summaries, and checksums are preserved in `artifacts/clock-host-20261019-0256-a533a80/`; the prior T01 batch remains in `artifacts/clock-20261019-0248-32194714/`. The previous worklog version is preserved there as `previous-worklog-README.md`; its SHA-256 still matches the old batch manifest (`568a60f274a4d9e97fb76c4d0e7d10d2c101116dae84f7e658d9bae91b8bcb16`). That earlier manifest records the pre-paired worklog snapshot and is not a checksum claim for this appended version.

Microsoft documents Hyper-V's time synchronization service as syncing a VM clock with the physical host and notes Linux integration drivers use `hv_utils` ([Hyper-V Integration Services](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/integration-services), [Manage Hyper-V Integration Services](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/Manage-Hyper-V-integration-services)). WSL release notes mention syncing WSL2 time with host time after resume ([WSL release notes](https://learn.microsoft.com/en-us/windows/wsl/release-notes?redirectedfrom=MSDN)). Windows Time documentation says it can discipline time by adjusting clock rate or directly changing clock time ([How the Windows Time Service works](https://learn.microsoft.com/en-us/windows-server/networking/windows-time-service/how-the-windows-time-service-works)); Microsoft documents `Stopwatch` as elapsed-time measurement backed by a high-resolution counter when supported ([Stopwatch class](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.stopwatch?view=netframework-4.8)). These references describe possible mechanisms, not evidence that any named mechanism caused this run.

The next read-only diagnostic target on this same machine is the WSL time-discipline path at the moment a step occurs; the captured unit/kernel journals had no matching entries. Do not change time services or clock settings based on this evidence alone.
