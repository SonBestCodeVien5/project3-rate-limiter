package main

import (
	"context"
	"flag"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"project3/ratelimiter/internal/console"
)

func main() {
	addr := flag.String("addr", "127.0.0.1:8090", "loopback listen address")
	flag.Parse()
	if host, _, err := net.SplitHostPort(*addr); err != nil || host != "127.0.0.1" {
		log.Fatal("-addr must use 127.0.0.1")
	}
	root, err := os.Getwd()
	if err != nil {
		log.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(root, "scripts/research-pilot.sh")); err != nil {
		log.Fatal("start from project root: ", err)
	}
	c, err := console.New(root)
	if err != nil {
		log.Fatal(err)
	}
	server := &http.Server{Addr: *addr, Handler: c.Handler(), ReadHeaderTimeout: 5 * time.Second}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	done := make(chan struct{})
	go func() {
		defer close(done)
		<-ctx.Done()
		shutdown, cancel := context.WithTimeout(context.Background(), 45*time.Second)
		defer cancel()
		_ = server.Shutdown(shutdown)
		if err := c.Shutdown(shutdown); err != nil {
			log.Printf("runner cleanup: %v", err)
		}
	}()
	log.Printf("Console: http://%s", *addr)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
	<-done
}
