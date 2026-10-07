# Project 3 brief

**Status:** no application code. [Experiment spec](../experiments/EXPERIMENT_SPEC.md) is a draft; architecture, quota parameters and tech stack are open.

Project 3 studies traffic control when an API scales from one instance with local state to multiple instances with Redis shared state. The business need is to protect backend services from unstable or abnormal traffic without losing quota correctness or creating excessive overhead. Project 2 was an application project; a broader traffic management platform belongs to the future graduation thesis.

**Project scope:** load balancer, API instances, Redis, Fixed Window, Token Bucket, load tests; compare normal, burst, concurrent and scaling behavior. Measure correctness/overshoot, p50/p95/p99 latency, requests per second and Redis CPU/memory. Sliding Window is optional. Full API Gateway, service mesh, production Kubernetes and full cloud infrastructure are outside scope.

**Open source differences:** Roadmap shows a traffic-control layer before API instances; Proposal depicts limiter with API instances. Roadmap includes atomic operations with Lua Script in research focus; Proposal marks Lua Script as an extension. Keep concurrency/atomicity in research scope and settle placement and mechanism during planning.

Read [SOURCE_INDEX.md](SOURCE_INDEX.md) for source priority and links. The local Markdown files are abridged repo notes; consult Drive for exact wording or missing detail.
