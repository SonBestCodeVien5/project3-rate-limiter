package console

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func request(t *testing.T, h http.Handler, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	r := httptest.NewRequest(method, path, strings.NewReader(body))
	if method == "POST" {
		r.Header.Set("Content-Type", "application/json")
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	return w
}

func TestRunLifecycleAndArtifacts(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, "scripts"), 0700); err != nil {
		t.Fatal(err)
	}
	script := filepath.Join(root, "scripts", "research-pilot.sh")
	if err := os.WriteFile(script, []byte("#!/bin/bash\nwhile (($#)); do if [[ $1 == --output ]]; then mkdir -p \"$2\"; fi; shift; done\nsleep 30\n"), 0700); err != nil {
		t.Fatal(err)
	}
	bin := t.TempDir()
	if err := os.WriteFile(filepath.Join(bin, "docker"), []byte("#!/bin/sh\nexit 0\n"), 0700); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", bin+":"+os.Getenv("PATH"))
	c, err := New(root)
	if err != nil {
		t.Fatal(err)
	}
	h := c.Handler()
	bad := request(t, h, "POST", "/api/runs", `{"case":"mixed-redis","repetitions":1,"mixed_rps":20}`)
	if bad.Code != 400 {
		t.Fatalf("invalid config: %d %s", bad.Code, bad.Body.String())
	}
	w := request(t, h, "POST", "/api/runs", `{"case":"mixed-redis","repetitions":1,"mixed_rps":120}`)
	if w.Code != 201 {
		t.Fatalf("start: %d %s", w.Code, w.Body.String())
	}
	var run Run
	if err := json.NewDecoder(bytes.NewReader(w.Body.Bytes())).Decode(&run); err != nil {
		t.Fatal(err)
	}
	if got := request(t, h, "POST", "/api/runs", `{"case":"mixed-none","repetitions":1,"mixed_rps":120}`); got.Code != 409 {
		t.Fatalf("concurrent run: %d", got.Code)
	}
	if got := request(t, h, "GET", "/api/runs/"+run.ID+"/artifacts/../request.json", ""); got.Code == 200 {
		t.Fatalf("path escape: %d", got.Code)
	}
	if got := request(t, h, "GET", "/api/runs/"+run.ID+"/artifacts/request.json", ""); got.Code != 200 {
		t.Fatalf("artifact: %d", got.Code)
	}
	if got := request(t, h, "POST", "/api/runs/"+run.ID+"/cancel", `{}`); got.Code != 202 {
		t.Fatalf("cancel: %d %s", got.Code, got.Body.String())
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		c.mu.Lock()
		state := c.runs[run.ID].State
		c.mu.Unlock()
		if state == "canceled" {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}
	c.mu.Lock()
	state := c.runs[run.ID].State
	c.mu.Unlock()
	if state != "canceled" {
		t.Fatalf("state=%s", state)
	}
	loaded, err := New(root)
	if err != nil || loaded.runs[run.ID].State != "canceled" {
		t.Fatalf("persisted state: %v %+v", err, loaded)
	}
}

func TestPostRequiresJSON(t *testing.T) {
	c, err := New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	r := httptest.NewRequest("POST", "/api/runs", strings.NewReader(`{"case":"mixed-redis","repetitions":1,"mixed_rps":120}`))
	r.Header.Set("Content-Type", "text/plain")
	w := httptest.NewRecorder()
	c.Handler().ServeHTTP(w, r)
	if w.Code != 415 {
		t.Fatalf("status=%d", w.Code)
	}
}

func TestRestartMarksUnfinishedRun(t *testing.T) {
	root := t.TempDir()
	c, err := New(root)
	if err != nil {
		t.Fatal(err)
	}
	r := &Run{ID: "20261011T120000-aabbccddeeff", State: "running", Request: Request{Case: "mixed-redis", Repetitions: 1, MixedRPS: 120}, Started: time.Now().UTC()}
	if err := os.MkdirAll(c.runDir(r.ID), 0700); err != nil {
		t.Fatal(err)
	}
	if err := c.save(r); err != nil {
		t.Fatal(err)
	}
	restarted, err := New(root)
	if err != nil {
		t.Fatal(err)
	}
	got := restarted.runs[r.ID]
	if got == nil || got.State != "interrupted" || got.Finished == nil {
		t.Fatalf("restart state: %+v", got)
	}
}
