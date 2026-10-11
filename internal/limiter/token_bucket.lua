local clock = redis.call('TIME')
local now = clock[1] * 1000 + math.floor(clock[2] / 1000)
local capacity = tonumber(ARGV[3])
local rate = tonumber(ARGV[4])
local state = redis.call('HMGET', KEYS[1], 'tokens', 'at')
local tokens = tonumber(state[1]) or capacity
local previous = tonumber(state[2]) or now
local effective = math.max(now, previous)
tokens = math.min(capacity, tokens + (effective - previous) * rate / 1000)
local allowed = 0
local retry = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
else
    retry = math.ceil((1 - tokens) * 1000 / rate) + effective - now
end
redis.call('HSET', KEYS[1], 'tokens', tostring(tokens), 'at', effective)
-- Expiry cannot recreate a full bucket before it would refill naturally.
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity * 1000 / rate) + effective - now)
return {allowed, math.floor(tokens), retry, now}
