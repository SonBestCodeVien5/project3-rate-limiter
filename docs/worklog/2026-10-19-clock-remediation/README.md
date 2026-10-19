# T01 single-controller clock remediation — 2026-10-19

## Result

At revision `f12170c06e27ee3740ce103136f286bd7f4aba7d`, Ubuntu WSL's `systemd-timesyncd` was active and enabled alongside the WSL system Chrony controller. Earlier direct tracing captured Chrony submitting successful `ADJ_TICK|ADJ_FREQUENCY`; the prior 90.100 s isolation showed no realtime residual steps while only Ubuntu timesyncd was stopped. This package made that isolation persistent for the current WSL distro: `systemctl disable --now systemd-timesyncd`. Windows time-service settings and all Chrony configuration were preserved.

Before changing the service, `state-before.txt` captured its active/enabled state, unit path, WSL drop-in, and MainPID. The drop-in documents timesyncd's role in synchronizing after host resume. The exact rollback is:

```sh
systemctl enable --now systemd-timesyncd
```

The final readback was `inactive`/`disabled` with MainPID 0. Restart and host-suspend/resume behavior were not tested. The packaged WSL drop-in's resume-sync behavior is therefore a known residual risk; re-enable timesyncd or establish an equivalent resume sync path if resume accuracy is required.

## Validation

After disabling timesyncd, Chrony remained available through `wsl --system`. Two tracking/source snapshots 20 seconds apart showed `#* PHC0`, stratum 1, reach 377, leap `Normal`, and the remaining correction decreasing from 0.435 µs to 0.214 µs. After the final observation, PHC0 remained selected with reach 377, stratum 1, leap `Normal`, remaining correction 1 ns, and estimated source error ±2.614 ms. Chrony's config still contains `server time.windows.com`, but the observed source list contained only PHC0; this does not establish external UTC accuracy.

The existing `scripts/observe-clock.py` then sampled for 90.0002 monotonic seconds (1,789 samples): zero adjacent wall-minus-monotonic steps exceeded 5 ms. Wall/monotonic elapsed ratio was `0.9999999805`. A concurrent endpoint sample measured MONOTONIC/RAW ratio `0.9999998935` over 90.0002 seconds. This passes the bounded current-session stability criterion only; no restart/resume durability is claimed.

Windows remained `W32Time=Stopped`, `StartType=Manual`, before and after. Read-only `w32tm /stripchart /packetinfo` queries to `time.windows.com` and `time.cloudflare.com` independently reported local-clock offsets of about +4.05 s. NTP originate timestamps followed by the receive/transmit timestamps show each remote clock was about four seconds ahead of Windows UTC; Microsoft documents stripchart as comparing the local computer with a remote computer and `packetinfo` as displaying the response packet. This remains a separate absolute UTC accuracy risk, not evidence of realtime steps or of Windows startup misconfiguration. No Windows service or startup settings were changed. [Microsoft W32tm documentation](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2-and-2012/ff799054%28v%3Dws.11%29)

Chrony's `System time` field is its remaining clock correction; the final value was 1 ns slow. The `#* PHC0` source marker denotes the selected local-clock source, not proof of external UTC synchronization. [Chrony `tracking` documentation](https://chrony-project.org/doc/3.1/chronyc.html)

No T03 load, benchmark, restart, or resume test ran. A final optional tick query attempted `/usr/bin/adjtimex`, which is absent in the WSL system distro; no tick write was attempted. The tracked [evidence archive](evidence.tar.gz) includes raw before/after state, observer samples and summary, Windows NTP packets, the observer source, and exact reproduction commands. The archive's inner [SHA256SUMS](SHA256SUMS) verified; outer archive SHA256 is `029f1468cbde768fd6e395852a78c3e29bdfa5758db5a255bd6840a561890832`.

## T01 status

**Current-session stability: pass.** **Absolute UTC accuracy and resume/restart durability: unverified.** T02 live gate validation remains pending, so T03 and later measurements remain gated.
