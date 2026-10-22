# T12 — demo/source package

## Scope and provenance

- Measured source revision: `0291a80fb404fea0eafee8c3431acc3631bb423e`.
- Demo/source checkout revision: `1c3f56dddc12bd405cd3d70ff1b553abda6c787c`. These revisions differ; the Console UI is a pilot presentation built after the measured source revision.
- `artifacts/t12/source-measurement/` is a `git archive` export for measured source, not a checkout. `artifacts/t12/source-demo/` is the compact runnable source snapshot. A detached Git checkout with LFS metadata is available at `/tmp/project3-t12-source`.
- T09 input archives were extracted under `/tmp/project3-t12-input/{v11,v12,v13}`. No source archive was rewritten. The detached checkout's Git and LFS status were clean before ignored saved-run restore.

## Saved pilot UI runs

The three final saved UI pilot runs were restored with their original Console Run IDs into the separate demo checkout `/tmp/project3-t12-source/artifacts/console/` and included in package V2 under `artifacts/console/`:

- `20261013T022629-bd56e4d4e3a5` — none.
- `20261013T022713-1011975d376e` — local; original clock/fidelity flags retained.
- `20261013T022742-f79870fc9be7` — Redis.

Their archive SHA-256 is `fa3c8eef86e2ef263dbde33fa07e06dfbef5c353e875b03a9ab060abb3ce25be`; all 36 file hashes per run match the original [manifest](../2026-10-13-console-content/evidence/manifest.json). Pilot source revision is `f608873643ed599defe19ede3694338214565318`. These UI values are pilot evidence only.

T09 protocol raw records use `p1-*` planned IDs and keep `custom-repeat-1` inside metadata; they are distinct from Console run IDs. Selected raw T09 records are retained separately in `artifacts/t12/saved-runs/`, with checksums matching T10's derived manifest. They are not presented as Console saved runs.

## Offline fallback

`artifacts/t12/offline/` contains T10 results, selected tables, run/traceability CSVs, original checksum index and all 11 existing figures copied without regeneration. All 41 entries in T10's original `SHA256SUMS` match. Fixed Window oracle remains `inconclusive`; refer to the full limitations in [T10_RESULTS.md](../../analysis/T10_RESULTS.md).

## Checks performed

- Extracted the original pilot archive only for the three named run folders; checked all 36 manifest hashes per run before and after restoring into the demo checkout.
- Built the demo Console successfully with Go caches under `/tmp`.
- Read-only GET verification returned 200 for `/api/runs`, each original saved run and each run's artifact listing. The browser selected the original three IDs and rendered the comparison table with status “Cấu hình và nội dung image khớp.” Detailed values and process status are in [checks](checks.txt).
- The temporary loopback server required a narrow sandbox escalation and was stopped. No POST, Docker load, benchmark, or live workload was issued.
- [Package V2](../../../artifacts/t12/PROJECT3-T12-DEMO-PACKAGE-v2.tar.gz) contains `artifacts/console/`, T10 offline fallback and compact demo source; SHA-256 `d11c6d79d26c8e2d5849e55a9c4c8fbc53a0cc1d4f44b49f333aa10b30c084d0`. Package V1 remains unchanged at SHA-256 `4eeb2c3d63e900eec7fc45c7fe46f85fa00dac8d65757d1a6ffd1045b18bbfab`.

## Limitations

The saved Console UI is still pilot evidence, not T10's formal result presentation. Use T10 offline artifacts for official measurement findings and preserve the separate source revisions. T13 rehearsal and slides are outside T12.
