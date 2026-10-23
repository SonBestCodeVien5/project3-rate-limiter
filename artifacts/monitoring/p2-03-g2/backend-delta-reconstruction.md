# Backend delta reconstruction

The earlier direct-backend comparison was not one isolated request. File mtimes from the saved command outputs establish this order (UTC):

- 13:58:18.821: backend JSON baseline: `arrivals=1`, `success=1`, `overload=0`.
- 13:58:24.789: API1 request 2 response file written; HTTP 200, `status=ok`.
- 13:58:31.905: direct backend request 3 response file written; HTTP 200, `status=ok`.
- 13:58:31.909: backend JSON after snapshot: `arrivals=3`, `success=3`, `overload=0`.

Thus the +2 arrivals/+2 success interval includes two completed requests: the API1 request and the direct backend request. The increment is explained by observed ordering and synchronous handler/proxy semantics; it was not a single-request backend delta test. The new isolated direct-backend request 5 has before/after JSON snapshots and returned HTTP 200: arrivals +1, success +1, overload +0.
