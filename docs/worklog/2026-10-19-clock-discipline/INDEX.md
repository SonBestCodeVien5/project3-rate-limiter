# Clock-discipline evidence index

Read [FOLLOWUP-v3.md](FOLLOWUP-v3.md) for the current interpretation: independently queried tick=9167 us, smooth RAW clock, and the corrected additive tick/frequency model. The clock-setting actor remains unknown; no system settings were changed.

Earlier versions are preserved as evidence, not competing conclusions:

- [README.md](README.md) / `evidence.tar.gz`: initial observation and NTP correlation; its raw-clock anomaly interpretation is superseded.
- [FOLLOWUP.md](FOLLOWUP.md) / `evidence-v2.tar.gz`: independent C validation; its preliminary multiplicative rate estimate is superseded.
- [FOLLOWUP-v3.md](FOLLOWUP-v3.md) / `evidence-v3.tar.gz`: corrected analysis and source caveats; manifests `SHA256SUMS-v3` and `ARCHIVE-SHA256SUMS-v3` validate this version.

The bounded temporary tick-restoration test and rollback are proposals requiring authorized scope before execution. No benchmark or clock-changing test ran.
