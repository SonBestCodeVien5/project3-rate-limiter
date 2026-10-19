# Analysis: closed-outage

Pilot observation; not a locked research conclusion.

Policy: `redis` / `fixed-window`; oracle: **inconclusive**.

Requests: 3000; sent: 3000; generator drops: 0.

Observed violations: 0. See `analysis.json` for scope and evidence.

## Redis outage

Availability uses legitimate successes divided by legitimate requests sent in each send-time phase.

- before: 73/81 legitimate successful/sent; availability 0.9012345679012346.
- pausing: 5/8 legitimate successful/sent; availability 0.625.
- outage: 0/40 legitimate successful/sent; availability 0.0.
- unpausing: 1/8 legitimate successful/sent; availability 0.125.
- after: 417/463 legitimate successful/sent; availability 0.9006479481641468.

Stable recovery: None ms (inconclusive).

Boundary windows, missing decisions and unknown prior state limit correctness claims. TB uses its own token semantics; FW quota is not applied to TB.
