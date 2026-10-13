# Study artifact report

Measured artifacts only. No winner or final research conclusion is inferred.

Business problem → pain point → business impact → technical requirement → solution → experiment → evaluation → future development must be supplied in the research report.

Tooling validity, correctness oracle and research claims are separate. FW inconclusive/partial windows do not invalidate a run by themselves. Errors/overload may be intended outcomes; flags require interpretation against the locked protocol.

Cell statistics are median/min/max of separate run metrics. A median of run p95/p99 is not a pooled percentile. No aggregation is exported for incomplete, incompatible or invalid-evidence cells.

Client clock check compares wall-clock sent−scheduled with monotonic schedule lag; it cannot diagnose server clock steps. Tolerance (ms): 5

| Cell | Runs / expected | Aggregation |
| --- | --- | --- |
| console-run/result | 2 / 2 | incompatible_config;invalid_run_evidence |
| mixed-local | 2 / 2 | incompatible_config;invalid_run_evidence |
| mixed-none | 2 / 2 | incompatible_config;invalid_run_evidence |
| mixed-redis | 2 / 2 | incompatible_config;invalid_run_evidence |
| normal-redis | 2 / 2 | incompatible_config;invalid_run_evidence |
| tb-burst1 | 2 / 2 | incompatible_config;invalid_run_evidence |
| tb-mixed2 | 2 / 2 | incompatible_config;invalid_run_evidence |

| Cell | Metric | Median of runs | Run min | Run max |
| --- | --- | --- | --- | --- |

| Run / repetition | Tooling | Oracle | Flags |
| --- | --- | --- | --- |
| custom-repeat-1 / 1 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-2 / 2 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-1 / 1 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed |
| custom-repeat-2 / 2 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed |
| custom-repeat-1 / 1 | invalid | not_applicable | dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed |
| custom-repeat-2 / 2 | invalid | not_applicable | dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed |
| custom-repeat-1 / 1 | invalid | inconclusive | client_clock_discontinuity_suspected;dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed;limiter_errors_observed |
| custom-repeat-2 / 2 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content;http_5xx_observed |
| custom-repeat-1 / 1 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-2 / 2 | invalid | inconclusive | dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-1 / 1 | invalid | no_violation_observed_within_trace | client_clock_discontinuity_suspected;dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-2 / 2 | invalid | no_violation_observed_within_trace | dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-1 / 1 | invalid | no_violation_observed_within_trace | client_clock_discontinuity_suspected;dirty_working_tree;dirty_working_tree_unverified_content |
| custom-repeat-2 / 2 | invalid | no_violation_observed_within_trace | dirty_working_tree;dirty_working_tree_unverified_content |

This exporter writes CSV/Markdown only. Use the separate offline plot-calibration.py for selected pilot charts; no runtime dependency was added.
