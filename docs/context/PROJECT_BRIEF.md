# Project 3 brief

Status: context initialized; the repository contains no application or experiment code. No implementation stack, limiter placement, quota semantics, or experiment parameters have been approved.

## Purpose and scope

**Project-defined.** The business problem is unstable or abnormal API traffic that can overload backend resources, raise latency, and disrupt service. Project 3 studies how traffic control behaves when a backend scales from one instance with local state to multiple instances with shared state. It builds a measurable distributed rate limiting prototype, rather than a complete API Gateway. Project 2 was a complete Gym Management application; a broader traffic management platform belongs to the later graduation thesis.

Core prototype: API instances, load balancer, Redis shared state, a rate limiter, Fixed Window, Token Bucket, load testing, and evaluation. Sliding Window is optional. Compare local state with Redis, one with multiple instances, and behavior under normal, burst, and concurrent traffic.

## Research questions and evidence

The Proposal asks how algorithms affect latency, throughput, and bursts; how shared state affects correctness and performance; what changes as instance count grows; and whether atomic operations improve concurrent correctness. The Roadmap calls for correctness, latency, throughput, and resource usage. Planned measures include allow/reject correctness, overshoot, p50/p95/p99 latency, requests per second, Redis CPU and memory. The Supplementary Research Context also proposes network overhead and burst recovery time. Treat its sample traffic rates and instance counts as examples, not approved parameters.

## Architecture and unresolved points

The documents agree on a minimal path involving a load balancer, multiple API instances, a limiter, and Redis. Their diagrams place the limiter differently: the Roadmap shows a traffic-control layer before backend instances, while the Proposal and Supplementary Research Context show a limiter associated with API instances. Resolve placement during planning; do not infer that a full gateway is required.

The Roadmap lists atomic operations with Redis Lua Script under core research; the Proposal lists Redis Lua Script as an extension. Keep atomicity and concurrency correctness in research scope under Roadmap priority. Decide the exact atomic mechanism and comparison design later.

## Boundaries and next decision

Outside Project 3: a full API Gateway, service mesh, production Kubernetes, and full cloud infrastructure. The broader thesis may add adaptive limits, circuit breakers, load shedding, retry control, multidimensional quotas, and observability-driven control.

**Engineering recommendation, not a project decision:** next define quota/key semantics, comparable algorithm configurations, limiter placement, and reproducible measurement procedures before selecting a stack or implementing code.

Source details and priority: [SOURCE_INDEX.md](SOURCE_INDEX.md).
