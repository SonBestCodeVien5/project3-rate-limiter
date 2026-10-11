package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/v9"
	"project3/ratelimiter/internal/limiter"
	"project3/ratelimiter/internal/server"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	if err := run(logger); err != nil {
		logger.Error("server stopped", "error", err)
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	cfg, err := server.LoadConfig(os.Getenv)
	if err != nil {
		return err
	}
	var l limiter.Limiter
	if cfg.Role == "api" {
		switch cfg.Mode {
		case "local":
			l, err = limiter.NewLocal(cfg.Policy)
		case "redis":
			client := redis.NewClient(&redis.Options{Addr: cfg.RedisAddr, MaxRetries: -1, ContextTimeoutEnabled: true, DialTimeout: cfg.RedisTimeout, ReadTimeout: cfg.RedisTimeout, WriteTimeout: cfg.RedisTimeout, PoolTimeout: cfg.RedisTimeout})
			defer client.Close()
			l, err = limiter.NewRedis(client, cfg.Policy, cfg.Namespace)
		}
	}
	if err != nil {
		return err
	}
	h := server.NewHandler(cfg, l, logger)
	defer h.Close()
	srv := &http.Server{Addr: cfg.ListenAddr, Handler: h, ReadHeaderTimeout: 3 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: cfg.BackendTimeout + cfg.RedisTimeout + 5*time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 16 << 10}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	result := make(chan error, 1)
	go func() { result <- srv.ListenAndServe() }()
	logger.Info("server started", "config", cfg)
	select {
	case err := <-result:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	case <-ctx.Done():
	}
	shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdown); err != nil {
		_ = srv.Close()
		return err
	}
	return nil
}
