# Offline Console demo package — 2026-10-19

Restored the archived Console triplet into the controller's saved-run directory using original `status.id` values. The existing Redis destination was preserved; none/local were copied from the mode-prefixed archive folders.

| Mode | Run ID | Clock/fidelity note |
| --- | --- | --- |
| None | `20261013T022629-bd56e4d4e3a5` | Passed saved-run quality flags |
| Local FW | `20261013T022713-1011975d376e` | Clock-quality failure preserved |
| Redis FW | `20261013T022742-f79870fc9be7` | Passed saved-run quality flags |

All three `status.json` IDs match their destination folder names. Per-file SHA-256 maps of each archived run directory and `artifacts/console/<id>/` matched exactly. No metadata or checksums were edited. The archived `evidence/manifest.json` referenced by the 2026-10-13 note was absent from this checkout, so verification used direct source-to-destination hashes.

Runs are short Console UI integration evidence, not formal benchmark results. The FW correctness oracle remains inconclusive; the local run retains its clock failure. Code/dataset consistency and a clean-checkout demo check remain pending T09–T10.
