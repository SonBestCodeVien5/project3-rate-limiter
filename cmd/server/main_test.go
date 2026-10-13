package main

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"project3/ratelimiter/internal/limiter"
	"project3/ratelimiter/internal/server"
)

type deadlineConn struct {
	net.Conn
	mu            sync.Mutex
	deadlines     []time.Time
	blockedWriter net.Conn
}

func (c *deadlineConn) SetReadDeadline(at time.Time) error {
	c.mu.Lock()
	c.deadlines = append(c.deadlines, at)
	c.mu.Unlock()
	return c.Conn.SetReadDeadline(at)
}
func (c *deadlineConn) SetWriteDeadline(at time.Time) error {
	c.mu.Lock()
	c.deadlines = append(c.deadlines, at)
	c.mu.Unlock()
	if c.blockedWriter != nil {
		if err := c.blockedWriter.SetWriteDeadline(at); err != nil {
			return err
		}
	}
	return c.Conn.SetWriteDeadline(at)
}
func (c *deadlineConn) Write(p []byte) (int, error) {
	if c.blockedWriter != nil && strings.Contains(string(p), "evalsha") {
		return c.blockedWriter.Write(p)
	}
	return c.Conn.Write(p)
}

func readCommand(r *bufio.Reader) ([]string, error) {
	line, err := r.ReadString('\n')
	if err != nil {
		return nil, err
	}
	n, err := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "*")))
	if err != nil {
		return nil, err
	}
	args := make([]string, n)
	for i := range args {
		line, err = r.ReadString('\n')
		if err != nil {
			return nil, err
		}
		size, e := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "$")))
		if e != nil {
			return nil, e
		}
		data := make([]byte, size+2)
		if _, err = io.ReadFull(r, data); err != nil {
			return nil, err
		}
		args[i] = string(data[:size])
	}
	return args, nil
}
func TestRedisContextOwnsSocketDeadlines(t *testing.T) {
	for _, scenario := range []string{"healthy-noscript", "blocked-handshake-read", "blocked-write", "blocked-command-read", "blocked-command-write", "blocked-noscript-read"} {
		t.Run(scenario, func(t *testing.T) {
			cfg := server.Config{RedisTimeout: 100 * time.Millisecond}
			client := newRedisClient(cfg)
			defer client.Close()
			opt := client.Options()
			if opt.ReadTimeout != 0 || opt.WriteTimeout != 0 || !opt.ContextTimeoutEnabled || opt.DialTimeout != cfg.RedisTimeout || opt.PoolTimeout != cfg.RedisTimeout || opt.MaxRetries != 0 {
				t.Fatalf("unexpected normalized options: %+v", opt)
			}
			local, remote := net.Pipe()
			defer remote.Close()
			captured := &deadlineConn{Conn: local}
			if scenario == "blocked-command-write" {
				a, b := net.Pipe()
				defer a.Close()
				defer b.Close()
				captured.blockedWriter = a
			}

			opt.Dialer = func(context.Context, string, string) (net.Conn, error) { return captured, nil }
			done := make(chan struct{})
			var commands []string
			go func() {
				defer close(done)
				if scenario == "blocked-write" {
					return
				}
				r := bufio.NewReader(remote)
				for {
					args, err := readCommand(r)
					if err != nil {
						return
					}
					command := strings.ToLower(args[0])
					commands = append(commands, command)
					if scenario == "blocked-handshake-read" || (command == "evalsha" && scenario == "blocked-command-read") || (command == "eval" && scenario == "blocked-noscript-read") {
						return
					}
					response := "-ERR unsupported command\r\n"
					if command == "evalsha" {
						response = "-NOSCRIPT No matching script\r\n"
					}
					if command == "eval" {
						response = "*4\r\n:1\r\n:19\r\n:0\r\n:1700000000000\r\n"
					}
					if _, err = fmt.Fprint(remote, response); err != nil {
						return
					}
				}
			}()
			ctx, cancel := context.WithTimeout(context.Background(), cfg.RedisTimeout)
			defer cancel()
			want, _ := ctx.Deadline()
			policy := limiter.Policy{Algorithm: limiter.FixedWindow, Limit: 20, Window: time.Second, Capacity: 20, Rate: 20}
			quota, err := limiter.NewRedis(client, policy, "deadline-test")
			if err != nil {
				t.Fatal(err)
			}
			start := time.Now()
			decision, err := quota.Allow(ctx, "key")
			elapsed := time.Since(start)
			if scenario == "healthy-noscript" {
				if err != nil || !decision.Allowed {
					t.Fatalf("healthy command: %+v %v", decision, err)
				}
			} else {
				if err == nil || elapsed < 70*time.Millisecond || elapsed > time.Second {
					t.Fatalf("bounded failure: elapsed=%v err=%v", elapsed, err)
				}
			}
			_ = remote.Close()
			<-done
			captured.mu.Lock()
			defer captured.mu.Unlock()
			if len(captured.deadlines) == 0 {
				t.Fatal("no socket deadlines")
			}
			for _, at := range captured.deadlines {
				if at != want {
					t.Fatalf("socket deadline %v differs from context %v", at, want)
				}
			}
			if scenario == "healthy-noscript" && !strings.Contains(strings.Join(commands, ","), "evalsha,eval") {
				t.Fatalf("NOSCRIPT fallback missing: %v", commands)
			}
		})
	}
}
