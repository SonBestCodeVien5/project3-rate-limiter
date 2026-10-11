package server

import (
	"fmt"
	"net/url"
	"strconv"
	"strings"
	"time"

	"project3/ratelimiter/internal/limiter"
)

type Config struct {
	Role, Mode, InstanceID, ListenAddr, RedisAddr, Namespace, FailPolicy string
	Policy                                                               limiter.Policy
	RedisTimeout, BackendTimeout, BackendServiceTime                     time.Duration
	BackendURL                                                           string
	BackendCapacity                                                      int
}

// LoadConfig accepts a lookup function to keep configuration tests isolated.
func LoadConfig(getenv func(string) string) (Config, error) {
	value := func(key, fallback string) string {
		if s := getenv(key); s != "" {
			return s
		}
		return fallback
	}
	c := Config{Role: value("ROLE", "api"), Mode: value("MODE", "local"), InstanceID: value("INSTANCE_ID", "api-1"), ListenAddr: value("LISTEN_ADDR", ":8080"), RedisAddr: value("REDIS_ADDR", "127.0.0.1:6379"), Namespace: value("NAMESPACE", "pilot"), FailPolicy: value("FAIL_POLICY", "closed"), BackendURL: value("BACKEND_URL", "http://127.0.0.1:8081")}
	c.Policy.Algorithm = value("ALGORITHM", "fixed-window")
	var err error
	for _, field := range []struct {
		key, fallback string
		dst           *int
	}{{"LIMIT", "20", &c.Policy.Limit}, {"CAPACITY", "20", &c.Policy.Capacity}, {"BACKEND_CAPACITY", "10", &c.BackendCapacity}} {
		*field.dst, err = strconv.Atoi(value(field.key, field.fallback))
		if err != nil {
			return c, fmt.Errorf("%s: %w", field.key, err)
		}
	}
	c.Policy.Rate, err = strconv.ParseFloat(value("RATE", "20"), 64)
	if err != nil {
		return c, fmt.Errorf("RATE: %w", err)
	}
	for _, field := range []struct {
		key, fallback string
		dst           *time.Duration
	}{{"WINDOW", "1s", &c.Policy.Window}, {"REDIS_TIMEOUT", "100ms", &c.RedisTimeout}, {"BACKEND_TIMEOUT", "2s", &c.BackendTimeout}, {"BACKEND_SERVICE_TIME", "50ms", &c.BackendServiceTime}} {
		*field.dst, err = time.ParseDuration(value(field.key, field.fallback))
		if err != nil {
			return c, fmt.Errorf("%s: %w", field.key, err)
		}
	}
	return c, c.Validate()
}

func (c Config) Validate() error {
	if c.Role != "api" && c.Role != "backend" {
		return fmt.Errorf("ROLE must be api or backend")
	}
	if c.Mode != "none" && c.Mode != "local" && c.Mode != "redis" {
		return fmt.Errorf("MODE must be none, local or redis")
	}
	if c.FailPolicy != "open" && c.FailPolicy != "closed" {
		return fmt.Errorf("FAIL_POLICY must be open or closed")
	}
	if err := c.Policy.Validate(); err != nil {
		return err
	}
	if strings.TrimSpace(c.InstanceID) == "" || strings.TrimSpace(c.Namespace) == "" || c.ListenAddr == "" || c.RedisAddr == "" {
		return fmt.Errorf("instance ID, namespace and addresses must not be empty")
	}
	if strings.ContainsAny(c.InstanceID, "\r\n") {
		return fmt.Errorf("INSTANCE_ID must not contain a newline")
	}
	if c.RedisTimeout <= 0 || c.BackendTimeout <= 0 || c.BackendServiceTime < 0 || c.BackendCapacity <= 0 {
		return fmt.Errorf("timeouts and backend capacity must be positive; service time must be nonnegative")
	}
	u, err := url.Parse(c.BackendURL)
	if err != nil || u.Host == "" || (u.Scheme != "http" && u.Scheme != "https") || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
		return fmt.Errorf("BACKEND_URL must be an HTTP(S) base URL without credentials, query or fragment")
	}
	return nil
}
