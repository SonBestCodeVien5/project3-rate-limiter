# T09 formal measurement handoff (partial)

The locked v1.1 study stopped at the mandatory clock gate for `p1-049-normal-none-r2`; no measurements were run after that finding. The package preserves 47 accepted planned run slots (the first 46 planned IDs plus accepted `p1-048`), all invalid/replacement attempts, and the 91 unaccepted planned IDs. It is not a complete study and does not contain T10 work or research conclusions.

The partial report exporter processed all 138 expected rows and all 46 cells at three expected repetitions each. It marks 47 rows usable and 91 invalid or unattempted; every cell is incomplete and has no aggregate. The separate `README-evidence.md` provides the handoff details. The archive contains the full raw traces/counters/configuration, ledger, observers, runtime images, locked manifest and protocol, pinned source snapshot, partial export, missing-ID list, retry-budget accounting, and exact launch/resume logs.

Measurement source: `0291a80fb404fea0eafee8c3431acc3631bb423e`. Locked manifest SHA-256: `32f8c6eb34bfd17e45b5dab5e1411b04ce410cf4b49c9ed495678fcb47fb3f79`. The p1-049 clock gate measured `294821.8144400488 ms` wall/monotonic residual and `16.0333/20 RPS`; the coordinator set `stop_sequence=true`. The separate `p1-047` slot exhausted its two replacement attempts after three `generator_drops` failures.

Archive SHA-256: `20f8d21845b8f381561ad293aef5b326d6bc85d63c39436e25ca9906a7e0a505`.

- [Full partial evidence archive](T09-FORMAL-PARTIAL-EVIDENCE.tar.gz)
- [Detailed evidence README](README-evidence.md)
- [Archive checksum](SHA256SUMS)
