# T08 stage 1: Redis network sampler live validation

**Outcome:** live validation now passes on clean revision b090d2b7391db873a0a2bbe602321ed1f5a55691. Redis network counters are cumulative bytes, the analyzer reports observed deltas from complete samples, and a TERM delivered during a live INFO cycle no longer leaves a partial sample. A matched 20 RPS API pair delivered 200/200 requests with sampling off and on. In that single pair, total Redis output rose from 844 B/s to 2,059 B/s with the sampler active; this includes INFO, healthchecks and workload traffic, so it indicates contamination but is not a calibrated correction.

The earlier fixed-revision attempt at d6163e7 exposed the shutdown race and remains preserved as invalid for network deltas in evidence/attempt-1/. Root committed the signal-deferred stop and regression test as b090d2b before the affected live recheck.

## Attempts and evidence

- attempt-1/: fresh 90-second observer passed at d6163e7; first Redis-only sampler run found a partial final sample on shutdown. Retain as the original invalid attempt. The observer output is reused for the same uninterrupted session.
- attempt-2/: clean fixed checkout b090d2b; live TERM-during-cycle check passed, followed by a matched API sampler-off/on pair. Full raw logs, load traces, resolved Compose config, image identities, analyzer output, commands, tests and checksums are archived there.
- attempt-2/invalid-attempts/: launcher failure before load and an equal-load pair where the sampler directory was absent. They are preserved and excluded from the valid comparison.

The dedicated Compose project project3-t08-validation was absent before startup and removed afterward. The final container/network checks are empty. Analyzer missing/reset rules and all thresholds are unchanged; the 20 analyzer tests cover missing samples and decreasing counters. No T01–T07 gate or full formal benchmark was repeated. T08 protocol is still not locked.

## Interpretation and limits

The sampler's three sequential Compose exec/INFO calls produced five complete snapshots at 2.29–2.42 second intervals, despite the one-second sleep. Counter values and analyzer rates are in bytes and bytes/second. The paired output-rate difference is a bounded indication of sampler/admin contamination; it includes INFO replies, healthchecks, boundary queries, and workload traffic. It does not establish limiter-only bytes/request, wire overhead, or a correction factor. A reset between observations can remain undetected.

For the matched pair and measured details, see [evidence/attempt-2/README.md](evidence/attempt-2/README.md). Keep both valid and invalid attempts with their own source revisions and checksum manifests.

## T08 stage 2 protocol lock

The new [versioned protocol](../../experiments/protocol-v1/protocol.md) and [planned manifest](../../experiments/protocol-v1/manifest.json) lock the 46-cell, 138-run plan at `b090d2b7391db873a0a2bbe602321ed1f5a55691`; this is documentation only and does not authorize T09. The archived Redis image inspect records image ID/digest `sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952` and `REDIS_VERSION=7.4.2`, matching `redis:7.4.2-alpine`. It does not contain a live `INFO server` response, so the protocol reports the immutable image and build metadata without claiming a separately observed server version.
