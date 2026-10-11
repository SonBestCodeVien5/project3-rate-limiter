package limiter

import (
	"context"
	"crypto/sha256"
	_ "embed"
	"fmt"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
)

//go:embed fixed_window.lua
var fixedWindowLua string

//go:embed token_bucket.lua
var tokenBucketLua string

type Redis struct {
	client *redis.Client
	policy Policy
	prefix string
	script *redis.Script
}

func NewRedis(client *redis.Client, p Policy, namespace string) (*Redis, error) {
	if err := p.Validate(); err != nil {
		return nil, err
	}
	if client == nil || strings.TrimSpace(namespace) == "" {
		return nil, fmt.Errorf("Redis client and namespace are required")
	}
	// Include the policy in the key to prevent state reuse across configurations.
	fingerprint := sha256.Sum256([]byte(fmt.Sprintf("%s:%d:%d:%d:%.17g", p.Algorithm, p.Limit, p.Window, p.Capacity, p.Rate)))
	script := fixedWindowLua
	if p.Algorithm == TokenBucket {
		script = tokenBucketLua
	}
	return &Redis{client: client, policy: p, prefix: fmt.Sprintf("p3:%s:%x:", namespace, fingerprint[:8]), script: redis.NewScript(script)}, nil
}

func (r *Redis) Allow(ctx context.Context, key string) (Decision, error) {
	hash := sha256.Sum256([]byte(key))
	p := r.policy
	values, err := r.script.Run(ctx, r.client, []string{fmt.Sprintf("%s%x", r.prefix, hash)}, p.Limit, p.Window.Milliseconds(), p.Capacity, p.Rate).Int64Slice()
	if err != nil {
		return Decision{}, fmt.Errorf("Redis quota decision: %w", err)
	}
	if len(values) != 4 {
		return Decision{}, fmt.Errorf("invalid Redis decision length: %d", len(values))
	}
	return Decision{Allowed: values[0] == 1, Remaining: int(values[1]), RetryAfter: time.Duration(values[2]) * time.Millisecond, At: time.UnixMilli(values[3])}, nil
}
