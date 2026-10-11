package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"

	"project3/ratelimiter/internal/experiment"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
func run() error {
	var c experiment.Config
	var out string
	flag.StringVar(&c.Target, "target", "http://localhost:8080/work", "Full /work URL")
	flag.StringVar(&c.RunID, "run-id", time.Now().UTC().Format("20060102T150405.000000000Z"), "Unique run identifier")
	flag.StringVar(&c.Profile, "profile", "mixed", "Workload profile: mixed, normal, burst, concurrent")
	flag.DurationVar(&c.Duration, "duration", 10*time.Second, "Offered load duration (maximum 10m)")
	flag.IntVar(&c.RPS, "rps", 100, "Total offered requests/second, including legitimate traffic")
	flag.IntVar(&c.LegitimateRPS, "legitimate-rps", 20, "Legitimate offered requests/second")
	flag.IntVar(&c.LegitimateClients, "legitimate-clients", 5, "Round-robin legitimate client keys")
	flag.IntVar(&c.MaxInflight, "max-inflight", 100, "Maximum concurrent HTTP requests")
	flag.DurationVar(&c.Timeout, "timeout", 2*time.Second, "Per-request timeout")
	flag.DurationVar(&c.MaxScheduleLag, "max-schedule-lag", 100*time.Millisecond, "Drop stale schedules rather than catch-up bursts")
	flag.DurationVar(&c.BurstStart, "burst-start", 0, "Burst phase start relative to run start")
	flag.DurationVar(&c.BurstDuration, "burst-duration", 0, "Finite burst phase duration")
	flag.IntVar(&c.BurstRPS, "burst-rps", 0, "Abusive requests/second during burst phase; must exceed baseline abusive rate")
	flag.DurationVar(&c.ConcurrentAt, "concurrent-at", 0, "Common scheduled instant of concurrent batch, relative to run start")
	flag.IntVar(&c.ConcurrentCount, "concurrent-count", 0, "Number of same-key requests in concurrent batch")
	flag.StringVar(&c.Mode, "mode", "unspecified", "Metadata label: none/local/redis")
	flag.StringVar(&c.Algorithm, "algorithm", "unspecified", "Metadata label: fixed-window/token-bucket")
	flag.StringVar(&c.FailPolicy, "fail-policy", "unspecified", "Metadata label: open/closed")
	flag.StringVar(&out, "out", "", "New artifact directory (default artifacts/<run-id>)")
	flag.Parse()
	if err := c.Validate(); err != nil {
		return err
	}
	if out == "" {
		if strings.ContainsAny(c.RunID, "/\\") || c.RunID == "." || c.RunID == ".." {
			return fmt.Errorf("run-id cannot contain a path separator")
		}
		out = filepath.Join("artifacts", c.RunID)
	}
	if err := os.MkdirAll(filepath.Dir(out), 0755); err != nil {
		return err
	}
	if err := os.Mkdir(out, 0755); err != nil {
		return fmt.Errorf("create new run directory: %w", err)
	}
	git := func(args ...string) string {
		b, err := exec.Command("git", args...).Output()
		if err != nil {
			return "unavailable"
		}
		return strings.TrimSpace(string(b))
	}
	host, _ := os.Hostname()
	metadata := map[string]any{"schema_version": 2, "workload_version": 2, "config": c, "command_argv": os.Args, "git_revision": git("rev-parse", "HEAD"), "git_status_porcelain": git("status", "--porcelain"), "go_version": runtime.Version(), "os": runtime.GOOS, "arch": runtime.GOARCH, "cpu_count": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0), "hostname": host, "recorded_at": time.Now().UTC(), "scope": "smoke/pilot; configuration labels do not verify server state"}
	writeJSON := func(name string, v any) error {
		b, err := json.MarshalIndent(v, "", "  ")
		if err != nil {
			return err
		}
		return os.WriteFile(filepath.Join(out, name), append(b, '\n'), 0644)
	}
	if err := writeJSON("metadata.json", metadata); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(out, "requests.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	summary, runErr := experiment.Run(ctx, c, f)
	closeErr := f.Close()
	if err := writeJSON("summary.json", summary); err != nil {
		return err
	}
	fmt.Printf("artifacts=%s sent=%d completed=%d dropped=%d legitimate_goodput=%.2f/s\n", out, summary.Sent, summary.Completed, summary.Dropped, summary.LegitimateGoodput)
	if runErr != nil {
		return runErr
	}
	if closeErr != nil {
		return closeErr
	}
	if ctx.Err() != nil {
		return ctx.Err()
	}
	return nil
}
