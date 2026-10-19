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
