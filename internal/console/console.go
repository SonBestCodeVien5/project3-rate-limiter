package console

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

var presets = map[string]string{"mixed-none": "Không limiter", "mixed-local": "State cục bộ", "mixed-redis": "State Redis dùng chung"}
var runID = regexp.MustCompile(`^[0-9]{8}T[0-9]{6}-[0-9a-f]{12}$`)

type Request struct {
	Case        string `json:"case"`
	Repetitions int    `json:"repetitions"`
	MixedRPS    int    `json:"mixed_rps"`
}

func (r Request) validate() error {
	if _, ok := presets[r.Case]; !ok {
		return errors.New("case must be mixed-none, mixed-local or mixed-redis")
	}
	if r.Repetitions < 1 || r.Repetitions > 3 {
		return errors.New("repetitions must be 1..3")
	}
	if r.MixedRPS < 21 || r.MixedRPS > 1000 {
		return errors.New("mixed_rps must be 21..1000")
	}
	return nil
}

type Run struct {
	ID         string     `json:"id"`
	Request    Request    `json:"request"`
	State      string     `json:"state"`
	Started    time.Time  `json:"started_at"`
	Finished   *time.Time `json:"finished_at,omitempty"`
	Error      string     `json:"error,omitempty"`
	CancelSent bool       `json:"cancel_requested,omitempty"`
	cmd        *exec.Cmd
}

type Controller struct {
	root, script string
	mu           sync.Mutex
	runs         map[string]*Run
	active       string
}

func New(root string) (*Controller, error) {
	root, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	c := &Controller{root: root, script: filepath.Join(root, "scripts/research-pilot.sh"), runs: make(map[string]*Run)}
	dirs, err := os.ReadDir(filepath.Join(root, "artifacts/console"))
	if errors.Is(err, os.ErrNotExist) {
		return c, nil
	}
	if err != nil {
		return nil, err
	}
	for _, dir := range dirs {
		if !dir.IsDir() || !runID.MatchString(dir.Name()) {
			continue
		}
		var r Run
		data, err := os.ReadFile(filepath.Join(c.runDir(dir.Name()), "status.json"))
		if err != nil || json.Unmarshal(data, &r) != nil || r.ID != dir.Name() {
			continue
		}
		if r.State == "starting" || r.State == "running" || r.State == "canceling" {
			finished := time.Now().UTC()
			r.State, r.Error, r.Finished = "interrupted", "Console restarted; inspect Docker project before starting another run", &finished
			_ = c.save(&r)
		}
		c.runs[r.ID] = &r
	}
	return c, nil
}

func (c *Controller) runDir(id string) string { return filepath.Join(c.root, "artifacts/console", id) }

func (c *Controller) save(r *Run) error {
	data, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return err
	}
	tmp := filepath.Join(c.runDir(r.ID), "status.json.tmp")
	if err := os.WriteFile(tmp, append(data, '\n'), 0600); err != nil {
		return err
	}
	return os.Rename(tmp, filepath.Join(c.runDir(r.ID), "status.json"))
}

func jsonResponse(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func (c *Controller) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = io.WriteString(w, page)
	})
	mux.HandleFunc("GET /api/presets", func(w http.ResponseWriter, _ *http.Request) {
		jsonResponse(w, 200, map[string]any{"presets": presets, "limits": map[string]any{"repetitions": []int{1, 3}, "mixed_rps": []int{21, 1000}}})
	})
	mux.HandleFunc("GET /api/demo", c.demo)
	mux.HandleFunc("POST /api/demo/request", c.demoRequest)
	mux.HandleFunc("GET /api/runs", c.list)
	mux.HandleFunc("POST /api/runs", c.start)
	mux.HandleFunc("GET /api/runs/{id}", c.get)
	mux.HandleFunc("POST /api/runs/{id}/cancel", c.cancel)
	mux.HandleFunc("GET /api/runs/{id}/metrics", c.metrics)
	mux.HandleFunc("GET /api/runs/{id}/artifacts", c.artifacts)
	mux.HandleFunc("GET /api/runs/{id}/artifacts/{name...}", c.artifact)
	return mux
}

func (c *Controller) demo(w http.ResponseWriter, req *http.Request) {
	client := &http.Client{Timeout: 2 * time.Second}
	result := map[string]any{}
	for name, url := range map[string]string{"health": "http://127.0.0.1:8080/healthz", "api1": "http://127.0.0.1:18081/metrics", "api2": "http://127.0.0.1:18082/metrics", "backend": "http://127.0.0.1:18083/metrics"} {
		response, err := client.Get(url)
		if err != nil {
			result[name] = map[string]string{"error": "unavailable"}
			continue
		}
		var value any
		err = json.NewDecoder(io.LimitReader(response.Body, 1<<20)).Decode(&value)
		_ = response.Body.Close()
		if err != nil || response.StatusCode != 200 {
			result[name] = map[string]string{"error": "invalid metrics response"}
		} else {
			result[name] = value
		}
	}
	jsonResponse(w, 200, map[string]any{"sampled_at": time.Now().UTC(), "source": "default Compose loopback ports; cumulative counters since container start", "samples": result})
}

func (c *Controller) demoRequest(w http.ResponseWriter, req *http.Request) {
	if req.Header.Get("Content-Type") != "application/json" || (req.Header.Get("Origin") != "" && req.Header.Get("Origin") != "http://"+req.Host) {
		jsonResponse(w, 403, map[string]string{"error": "cross-origin request refused"})
		return
	}
	client := &http.Client{Timeout: 3 * time.Second}
	work, _ := http.NewRequestWithContext(req.Context(), http.MethodPost, "http://127.0.0.1:8080/work", nil)
	work.Header.Set("X-Client-ID", "console-demo")
	response, err := client.Do(work)
	if err != nil {
		jsonResponse(w, 503, map[string]string{"error": "default Compose ingress unavailable"})
		return
	}
	defer response.Body.Close()
	var body any
	_ = json.NewDecoder(io.LimitReader(response.Body, 1<<20)).Decode(&body)
	jsonResponse(w, 200, map[string]any{"http_status": response.StatusCode, "decision": response.Header.Get("X-Limiter-Decision"), "instance": response.Header.Get("X-Instance-ID"), "backend_arrival": response.Header.Get("X-Backend-Arrival"), "body": body})
}

func (c *Controller) list(w http.ResponseWriter, _ *http.Request) {
	c.mu.Lock()
	defer c.mu.Unlock()
	items := make([]Run, 0, len(c.runs))
	for _, r := range c.runs {
		items = append(items, *r)
	}
	jsonResponse(w, 200, items)
}

func (c *Controller) start(w http.ResponseWriter, req *http.Request) {
	if req.Header.Get("Content-Type") != "application/json" || (req.Header.Get("Origin") != "" && req.Header.Get("Origin") != "http://"+req.Host) {
		jsonResponse(w, 415, map[string]string{"error": "Content-Type must be application/json"})
		return
	}
	var config Request
	dec := json.NewDecoder(http.MaxBytesReader(w, req.Body, 4096))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&config); err != nil {
		jsonResponse(w, 400, map[string]string{"error": err.Error()})
		return
	}
	if dec.Decode(new(any)) != io.EOF {
		jsonResponse(w, 400, map[string]string{"error": "one JSON object required"})
		return
	}
	if err := config.validate(); err != nil {
		jsonResponse(w, 400, map[string]string{"error": err.Error()})
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.active != "" {
		jsonResponse(w, 409, map[string]string{"error": "another run is active"})
		return
	}
	var random [6]byte
	if _, err := rand.Read(random[:]); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	id := time.Now().UTC().Format("20060102T150405") + "-" + hex.EncodeToString(random[:])
	dir := c.runDir(id)
	if err := os.MkdirAll(filepath.Dir(dir), 0700); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	if err := os.Mkdir(dir, 0700); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	r := &Run{ID: id, Request: config, State: "starting", Started: time.Now().UTC()}
	if err := c.save(r); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	data, _ := json.MarshalIndent(config, "", "  ")
	if err := os.WriteFile(filepath.Join(dir, "request.json"), append(data, '\n'), 0600); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	log, err := os.Create(filepath.Join(dir, "runner.log"))
	if err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	cmd := exec.Command("bash", c.script, "--output", filepath.Join(dir, "result"), "--case", config.Case, "--repetitions", strconv.Itoa(config.Repetitions), "--analyze")
	cmd.Dir, cmd.Stdout, cmd.Stderr = c.root, log, log
	cmd.Env = append(os.Environ(), "MIXED_RPS="+strconv.Itoa(config.MixedRPS))
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	c.runs[id] = r
	if err := cmd.Start(); err != nil {
		_ = log.Close()
		finished := time.Now().UTC()
		r.State, r.Error, r.Finished = "failed", err.Error(), &finished
		_ = c.save(r)
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	r.cmd, r.State, c.active = cmd, "running", id
	_ = c.save(r)
	go c.wait(r, log)
	jsonResponse(w, 201, r)
}

func (c *Controller) wait(r *Run, log *os.File) {
	err := r.cmd.Wait()
	_ = log.Close()
	c.mu.Lock()
	r.cmd = nil
	c.mu.Unlock()
	// The runner's trap owns cleanup; this check catches failed cleanup after cancel or failure.
	check := exec.Command("timeout", "10s", "docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=project3-research-lab")
	output, checkErr := check.Output()
	c.mu.Lock()
	defer c.mu.Unlock()
	finished := time.Now().UTC()
	r.Finished = &finished
	switch {
	case r.CancelSent:
		r.State = "canceled"
	case err != nil:
		r.State, r.Error = "failed", err.Error()
	default:
		r.State = "completed"
	}
	if checkErr != nil {
		r.State, r.Error = "cleanup-error", "cannot verify research Compose project cleanup"
	} else if len(strings.TrimSpace(string(output))) > 0 {
		r.State, r.Error = "cleanup-error", "research Compose project still has containers"
	}
	c.active = ""
	_ = c.save(r)
}

func (c *Controller) lookup(w http.ResponseWriter, req *http.Request) *Run {
	id := req.PathValue("id")
	if !runID.MatchString(id) {
		http.NotFound(w, req)
		return nil
	}
	c.mu.Lock()
	r := c.runs[id]
	c.mu.Unlock()
	if r == nil {
		http.NotFound(w, req)
	}
	return r
}

func (c *Controller) get(w http.ResponseWriter, req *http.Request) {
	r := c.lookup(w, req)
	if r == nil {
		return
	}
	c.mu.Lock()
	snapshot := *r
	c.mu.Unlock()
	result := map[string]any{"run": snapshot}
	phase := snapshot.State
	if snapshot.State == "running" {
		phase = "preparing"
		for i := 1; i <= snapshot.Request.Repetitions; i++ {
			caseDir := filepath.Join(c.runDir(r.ID), "result", fmt.Sprintf("%s-repeat-%d", r.Request.Case, i))
			if _, err := os.Stat(filepath.Join(caseDir, "topology", "compose.json")); err == nil {
				phase = fmt.Sprintf("starting repeat %d", i)
			}
			if _, err := os.Stat(filepath.Join(caseDir, "load")); err == nil {
				phase = fmt.Sprintf("running/draining repeat %d", i)
			}
			if _, err := os.Stat(filepath.Join(caseDir, "load", "summary.json")); err == nil {
				phase = fmt.Sprintf("analyzing repeat %d", i)
			}
			if _, err := os.Stat(filepath.Join(caseDir, "analysis.json")); err == nil {
				phase = fmt.Sprintf("cleanup repeat %d", i)
			}
		}
	}
	result["phase"] = phase
	summaries := map[string]any{}
	for i := 1; i <= r.Request.Repetitions; i++ {
		if data, err := os.ReadFile(filepath.Join(c.runDir(r.ID), "result", fmt.Sprintf("%s-repeat-%d", r.Request.Case, i), "load", "summary.json")); err == nil {
			var summary any
			if json.Unmarshal(data, &summary) == nil {
				summaries[strconv.Itoa(i)] = summary
			}
		}
	}
	result["summaries"] = summaries
	caseDir := filepath.Join(c.runDir(r.ID), "result", r.Request.Case+"-repeat-1")
	if data, err := os.ReadFile(filepath.Join(caseDir, "policy.json")); err == nil {
		var policy any
		if json.Unmarshal(data, &policy) == nil {
			result["resolved_policy"] = policy
		}
	}
	if data, err := os.ReadFile(filepath.Join(caseDir, "compose-resolved.json")); err == nil {
		var compose struct {
			Services map[string]struct {
				Environment map[string]any `json:"environment"`
			} `json:"services"`
		}
		if json.Unmarshal(data, &compose) == nil {
			result["resolved_backend"] = compose.Services["backend"].Environment
		}
	}
	jsonResponse(w, 200, result)
}

func (c *Controller) cancel(w http.ResponseWriter, req *http.Request) {
	if req.Header.Get("Content-Type") != "application/json" || (req.Header.Get("Origin") != "" && req.Header.Get("Origin") != "http://"+req.Host) {
		jsonResponse(w, 403, map[string]string{"error": "cross-origin request refused"})
		return
	}
	r := c.lookup(w, req)
	if r == nil {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.active != r.ID || r.cmd == nil || r.CancelSent {
		jsonResponse(w, 409, map[string]string{"error": "run is not cancelable"})
		return
	}
	if err := syscall.Kill(-r.cmd.Process.Pid, syscall.SIGTERM); err != nil {
		jsonResponse(w, 500, map[string]string{"error": err.Error()})
		return
	}
	r.CancelSent, r.State = true, "canceling"
	_ = c.save(r)
	jsonResponse(w, 202, r)
}

func (c *Controller) Shutdown(ctx context.Context) error {
	c.mu.Lock()
	id := c.active
	c.mu.Unlock()
	if id == "" {
		return nil
	}
	c.mu.Lock()
	r := c.runs[id]
	if r != nil && r.cmd != nil && !r.CancelSent {
		_ = syscall.Kill(-r.cmd.Process.Pid, syscall.SIGTERM)
		r.CancelSent = true
		r.State = "canceling"
		_ = c.save(r)
	}
	c.mu.Unlock()
	tick := time.NewTicker(100 * time.Millisecond)
	defer tick.Stop()
	for {
		c.mu.Lock()
		active := c.active
		c.mu.Unlock()
		if active == "" {
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-tick.C:
		}
	}
}

func (c *Controller) metrics(w http.ResponseWriter, req *http.Request) {
	r := c.lookup(w, req)
	if r == nil {
		return
	}
	c.mu.Lock()
	active := c.active == r.ID
	c.mu.Unlock()
	if !active {
		jsonResponse(w, 200, map[string]string{"status": "no live sample; see saved before/after metrics"})
		return
	}
	caseDir := ""
	for i := r.Request.Repetitions; i >= 1; i-- {
		candidate := filepath.Join(c.runDir(r.ID), "result", fmt.Sprintf("%s-repeat-%d", r.Request.Case, i), "topology", "compose.json")
		if _, err := os.Stat(candidate); err == nil {
			caseDir = candidate
			break
		}
	}
	if caseDir == "" {
		jsonResponse(w, 200, map[string]string{"status": "waiting for lab startup"})
		return
	}
	ctx, cancel := context.WithTimeout(req.Context(), 5*time.Second)
	defer cancel()
	samples := map[string]any{}
	for _, service := range []string{"api1", "api2", "backend"} {
		cmd := exec.CommandContext(ctx, "docker", "compose", "--project-directory", c.root, "-f", caseDir, "-p", "project3-research-lab", "exec", "-T", service, "wget", "-q", "-O", "-", "http://127.0.0.1:8080/metrics")
		data, err := cmd.Output()
		if err == nil {
			var value any
			if json.Unmarshal(data, &value) == nil {
				samples[service] = value
			}
		}
	}
	jsonResponse(w, 200, map[string]any{"sampled_at": time.Now().UTC(), "source": "Docker exec /metrics; cumulative counters since container start", "samples": samples})
}

var caseArtifacts = []string{"compose-resolved.json", "policy.json", "load/summary.json", "load/metadata.json", "load/requests.jsonl", "analysis.json", "analysis.md", "compose.log", "redis-resources.log", "api1-before.json", "api1-after.json", "api2-before.json", "api2-after.json", "backend-before.json", "backend-after.json"}

func (c *Controller) artifactPaths(r *Run) map[string]string {
	paths := map[string]string{}
	dir := c.runDir(r.ID)
	for _, name := range []string{"runner.log", "request.json", "status.json"} {
		paths[name] = filepath.Join(dir, name)
	}
	for _, name := range []string{"git-revision.txt", "git-status.txt"} {
		paths[name] = filepath.Join(dir, "result", name)
	}
	for i := 1; i <= r.Request.Repetitions; i++ {
		prefix := fmt.Sprintf("%s-repeat-%d", r.Request.Case, i)
		for _, name := range caseArtifacts {
			paths[prefix+"/"+name] = filepath.Join(dir, "result", prefix, name)
		}
	}
	return paths
}

func (c *Controller) artifacts(w http.ResponseWriter, req *http.Request) {
	r := c.lookup(w, req)
	if r == nil {
		return
	}
	items := []string{}
	for name, path := range c.artifactPaths(r) {
		if info, err := os.Lstat(path); err == nil && info.Mode().IsRegular() {
			items = append(items, name)
		}
	}
	jsonResponse(w, 200, items)
}

func (c *Controller) artifact(w http.ResponseWriter, req *http.Request) {
	r := c.lookup(w, req)
	if r == nil {
		return
	}
	path, ok := c.artifactPaths(r)[req.PathValue("name")]
	if !ok {
		http.NotFound(w, req)
		return
	}
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() {
		http.NotFound(w, req)
		return
	}
	w.Header().Set("Content-Disposition", "attachment; filename="+strconv.Quote(filepath.Base(path)))
	http.ServeFile(w, req, path)
}
