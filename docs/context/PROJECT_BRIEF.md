# Project 3 brief

**Conversation workspace:** [ChatGPT Project 3](https://chatgpt.com/g/g-p-6ac5bc31497c81919197782e9d2226c6-project3/project) (link supplied by the user). This is a navigation link, not an authoritative source of project requirements; use [SOURCE_INDEX.md](SOURCE_INDEX.md) for source priority.

**Status:** Week 1 business framing and scope are complete, but the foundational knowledge self-check is pending; Week 1 overall remains in progress. Week 2 policy work has not started. There is no application code. The project direction was rebased on 2026-10-08 to include backend protection and a bounded Redis-outage experiment. The [roadmap to defense](../PROJECT_ROADMAP.md) and [experiment spec](../experiments/EXPERIMENT_SPEC.md) remain drafts; architecture, quota parameters and tech stack are open.

The adviser accepted the topic and asked for stronger business-problem framing. The user selected a hypothetical e-commerce flash sale scenario; the Drive Proposal now includes its pain point, business impact and evaluation link. Required hand-in items are report, source code, slides and demo; the deadline is tentatively in the last 2–3 weeks of December 2026. Exact dates and grading rubric are unknown. See the [Week 1 business case](../WEEK1_BUSINESS_CASE.md).

Project 3 studies traffic control when an API scales from one instance with local state to multiple instances with Redis shared state. The business need is to protect backend services from unstable or abnormal traffic without losing quota correctness or creating excessive overhead. Project 2 was an application project; a broader traffic management platform belongs to the future graduation thesis.

**Project scope:** load balancer, API instances, Redis, Fixed Window, Token Bucket, load tests; compare normal, burst, concurrent and scaling behavior. The updated baseline also compares no limiter/local/Redis shared under mixed legitimate and abusive traffic, and performs a short controlled Redis outage to evaluate explicit fail-open/fail-closed behavior. Measure correctness/overshoot, p50/p95/p99 latency, requests per second, Redis CPU/memory, legitimate-client goodput and tail latency, backend arrivals, 429 versus timeout/5xx, quota violation and recovery. Sliding Window, dashboard and complex policy management are optional. Full API Gateway, Redis Cluster/production HA, service mesh, production Kubernetes and full cloud infrastructure are outside scope.

The updated Proposal has five research questions: the original algorithm, state, scaling and atomicity questions plus RQ5 on legitimate-client protection under overload and the Redis-outage trade-off. The project title is unchanged.

**Open source difference:** Roadmap shows a traffic-control layer before API instances; Proposal depicts limiter with API instances. Atomicity is core in both updated sources; Lua Script is one possible mechanism, and comparison with another mechanism remains optional. Settle placement and mechanism during planning.

Read [SOURCE_INDEX.md](SOURCE_INDEX.md) for source priority and links. The local Markdown files are abridged repo notes; consult Drive for exact wording or missing detail.
