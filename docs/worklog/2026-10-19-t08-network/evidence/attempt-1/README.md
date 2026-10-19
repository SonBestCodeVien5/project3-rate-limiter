# Initial T08 live attempt on d6163e7

This attempt ran on detached fixed revision d6163e7f40da1fd47e3ce2b8e48e70c702426062 with Redis 7.4.2 and Docker Engine 29.3.1 / Compose 5.1.1. A fresh 90-second clock observer ran before Docker: 1,791 samples, zero wall/monotonic steps above 5 ms. Observer raw data and summary are preserved here.

The Redis-only check confirmed cumulative INFO stats counters move in bytes after client traffic. During a 10-second sampler interval, the process was terminated during an INFO cycle. The raw log contains five timestamp records but only four complete CPU/memory/stats snapshots; the final record ends after CPU. The analyzer marked both network directions incomplete. This is the valid observation that exposed the shutdown race, while the captured network delta itself is invalid.

The root later committed the signal-deferred stop and lifecycle test as b090d2b. The fixed-source live TERM test and matched sampler-off/on API pair are recorded in attempt-2/README.md. This original failed attempt remains unchanged for audit.

The idle and sampler intervals were only a single rough comparison. INFO, Redis healthchecks, and snapshot boundary queries are included in counters; resets between samples may remain undetected. No bytes/request, limiter-only traffic, wire overhead, or sampler correction can be inferred. The dedicated Docker project was removed; the cleanup transcript is preserved.
