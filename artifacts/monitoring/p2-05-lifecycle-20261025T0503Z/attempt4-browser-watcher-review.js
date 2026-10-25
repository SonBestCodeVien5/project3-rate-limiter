// Test-only watcher for the existing Console UI. Install before clicking #run.
// It never starts a run and never calls the cancel endpoint: cancellation is
// dispatched only by clicking the existing #cancel DOM button.
async () => {
  const key = "__p205CancelWatcher";
  if (window[key]?.armed) throw new Error("P2-05 cancellation watcher already armed");
  const result = {
    armed: true,
    baseline_ready: false,
    form_verified: false,
    error: null,
    installed_at_utc: new Date().toISOString(),
    watchdog_ms: 180000,
    baseline_run_ids: [],
    run_id: null,
    config_verified: false,
    metric_observations: 0,
    active_metric_at_utc: null,
    active_requests: null,
    cancel_dom_click_at_utc: null,
    cancel_response_status: null,
    cancel_response_at_utc: null,
    terminal_before_signal: false,
    finished_at_utc: null,
  };
  window[key] = result;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const now = () => new Date().toISOString();
  const idFromPage = () => (document.querySelector("#state")?.textContent || "").match(/\b(20\d{6}T\d{6}-[a-f0-9]{12})\b/)?.[1] || null;
  const isTerminal = state => ["completed", "failed", "canceled", "cleanup-error"].includes(state);
  const initialFetch = window.fetch.bind(window);
  let resolveReady;
  const ready = new Promise(resolve => { resolveReady = resolve; });
  let wrappedFetch = null;
  const restoreFetch = () => { if (wrappedFetch && window.fetch === wrappedFetch) window.fetch = initialFetch; };
  const deadline = Date.now() + result.watchdog_ms;
  const boundedFetch = (url, init = {}) => {
    const remaining = Math.max(1, deadline - Date.now());
    return initialFetch(url, { ...init, signal: AbortSignal.timeout(Math.min(8000, remaining)) });
  };
  let finished = false;
  let watchdogTimer = null;
  const finish = error => {
    if (finished) return;
    finished = true;
    if (error && !result.error) result.error = String(error?.message || error);
    clearTimeout(watchdogTimer);
    restoreFetch();
    result.armed = false;
    result.finished_at_utc = now();
  };

  (async () => {
    const form = {
      preset: document.querySelector("#preset")?.value,
      profile: document.querySelector("#profile")?.value,
      mode: document.querySelector("#mode")?.value,
      algorithm: document.querySelector("#algorithm")?.value,
      failPolicy: document.querySelector("#failPolicy")?.value,
      instances: Number(document.querySelector("#instances")?.value),
      rps: Number(document.querySelector("#totalRps")?.value),
      legitimateRps: Number(document.querySelector("#legitRps")?.value),
      duration: Number(document.querySelector("#duration")?.value),
      limit: Number(document.querySelector("#limit")?.value),
      windowMs: Number(document.querySelector("#windowMs")?.value),
      backendCapacity: Number(document.querySelector("#backendCapacity")?.value),
      backendServiceMs: Number(document.querySelector("#backendService")?.value),
      repetitions: Number(document.querySelector("#repetitions")?.value),
      monitoring: document.querySelector("#monitoring")?.checked,
    };
    result.approved_form_config = form;
    result.form_verified = form.preset === "custom" && form.profile === "normal" &&
      form.mode === "redis" && form.algorithm === "fixed-window" && form.failPolicy === "closed" &&
      form.instances === 2 && form.rps === 20 && form.legitimateRps === 20 && form.duration === 30 &&
      form.limit === 20 && form.windowMs === 1000 && form.backendCapacity === 4 &&
      form.backendServiceMs === 50 && form.repetitions === 1 && form.monitoring === true;
    if (!result.form_verified) throw new Error("Console form did not match approved cancellation scenario");

    const runsResponse = await boundedFetch("/api/runs", { cache: "no-store" });
    if (!runsResponse.ok) throw new Error(`baseline /api/runs returned ${runsResponse.status}`);
    result.baseline_run_ids = (await runsResponse.json()).map(run => run.id);
    result.baseline_ready = true;
    result.error = null;
    resolveReady({ armed: result.armed, baseline_ready: true, form_verified: result.form_verified,
      watchdog_ms: result.watchdog_ms, method: "read Console /api/runs/{id}/metrics; click #cancel DOM only" });

    while (Date.now() < deadline && !result.run_id) {
      const candidate = idFromPage();
      if (candidate && !result.baseline_run_ids.includes(candidate)) result.run_id = candidate;
      else await sleep(100);
    }
    if (!result.run_id) throw new Error("no new Console-selected run before 180s watchdog");

    const runResponse = await boundedFetch(`/api/runs/${result.run_id}`, { cache: "no-store" });
    if (!runResponse.ok) throw new Error(`selected run lookup returned ${runResponse.status}`);
    const run = (await runResponse.json()).run;
    const c = run?.request?.custom || {};
    result.config_verified = run?.request?.case === "custom" && run.request.monitoring === true &&
      run.request.repetitions === 1 && c.profile === "normal" && c.mode === "redis" &&
      c.algorithm === "fixed-window" && c.fail_policy === "closed" && c.instances === 2 &&
      c.rps === 20 && c.legitimate_rps === 20 && c.duration_seconds === 30 &&
      c.limit === 20 && c.window_ms === 1000 && c.backend_capacity === 4 &&
      c.backend_service_ms === 50;
    if (!result.config_verified) throw new Error("new run config did not match approved cancellation scenario");

    wrappedFetch = function(input, init) {
      const url = typeof input === "string" ? input : input?.url || "";
      const method = (init?.method || input?.method || "GET").toUpperCase();
      const isUICancel = url.endsWith(`/api/runs/${result.run_id}/cancel`) && method === "POST";
      if (isUICancel) result.cancel_request_started_at_utc = now();
      return initialFetch(input, init).then(response => {
        if (isUICancel) {
          result.cancel_response_status = response.status;
          result.cancel_response_at_utc = now();
        }
        return response;
      }, error => {
        if (isUICancel) result.cancel_response_error = String(error);
        throw error;
      });
    };
    window.fetch = wrappedFetch;

    while (Date.now() < deadline) {
      const stateText = document.querySelector("#state")?.textContent || "";
      if (!stateText.includes(result.run_id)) throw new Error("Console selection changed before cancellation");
      if (/\b(completed|failed|canceled|cleanup-error)\b/.test(stateText)) {
        result.terminal_before_signal = true;
        throw new Error("selected run became terminal before live request metric appeared");
      }
      const response = await boundedFetch(`/api/runs/${result.run_id}/metrics`, { cache: "no-store" });
      if (!response.ok) throw new Error(`Console metrics returned ${response.status}`);
      const metric = await response.json();
      result.metric_observations++;
      if (metric.samples && Object.keys(metric.samples).some(service => /^api[1-4]$/.test(service) &&
          Number(metric.samples[service]?.requests) > 0)) {
        result.active_metric_at_utc = now();
        result.active_requests = Object.fromEntries(Object.entries(metric.samples)
          .filter(([service]) => /^api[1-4]$/.test(service))
          .map(([service, sample]) => [service, sample?.requests ?? null]));
        const button = document.querySelector("#cancel");
        if (!button || button.disabled) throw new Error("live API request observed but Hủy button was not enabled");
        if (idFromPage() !== result.run_id) throw new Error("run selection changed at cancellation point");
        result.cancel_dom_click_at_utc = now();
        button.click();
        return;
      }
      await sleep(100);
    }
    throw new Error("no live API request metric before 180s watchdog");
  })().catch(error => {
    finish(error);
    resolveReady({ armed: result.armed, baseline_ready: result.baseline_ready,
      form_verified: result.form_verified, watchdog_ms: result.watchdog_ms, error: result.error });
  }).finally(() => finish());
  watchdogTimer = setTimeout(() => finish(new Error("180s watcher watchdog expired")), result.watchdog_ms);

  return await ready;
}
