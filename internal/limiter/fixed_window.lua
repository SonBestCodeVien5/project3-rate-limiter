-- Only this script reads, decides and mutates the shared quota.
local clock = redis.call('TIME')
local now = clock[1] * 1000 + math.floor(clock[2] / 1000)
local limit = tonumber(ARGV[1])
local width = tonumber(ARGV[2])
local window = math.floor(now / width)
local state = redis.call('HMGET', KEYS[1], 'window', 'count')
local count = 0
if tonumber(state[1]) == window then count = tonumber(state[2]) or 0 end
local allowed = 0
local retry = 0
if count < limit then
    count = count + 1
    allowed = 1
    redis.call('HSET', KEYS[1], 'window', window, 'count', count)
    redis.call('PEXPIREAT', KEYS[1], (window + 1) * width)
else
    retry = (window + 1) * width - now
end
return {allowed, limit - count, retry, now}
