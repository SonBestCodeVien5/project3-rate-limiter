# Analysis: open-outage

Pilot observation; not a locked research conclusion.

Policy: `redis` / `fixed-window`; oracle: **inconclusive**.

Requests: 3000; sent: 3000; generator drops: 0.

Observed violations: 0. See `analysis.json` for scope and evidence.

## Redis outage

Availability uses legitimate successes divided by legitimate requests sent in each send-time phase.

- before: 67/81 legitimate successful/sent; availability 0.8271604938271605.
- pausing: 7/9 legitimate successful/sent; availability 0.7777777777777778.
- outage: 18/40 legitimate successful/sent; availability 0.45.
- unpausing: 3/7 legitimate successful/sent; availability 0.42857142857142855.
- after: 401/463 legitimate successful/sent; availability 0.8660907127429806.

Stable recovery: None ms (inconclusive).

Boundary windows, missing decisions and unknown prior state limit correctness claims. TB uses its own token semantics; FW quota is not applied to TB.
