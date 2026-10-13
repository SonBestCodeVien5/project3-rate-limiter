#!/usr/bin/env python3
"""Derive calibration evidence without altering raw files."""
import csv, datetime as dt, json, math, pathlib, sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); rows=[]
def read(p): return json.loads(p.read_text())
def epoch(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def p95(xs): return sorted(xs)[math.ceil(.95*len(xs))-1] if xs else None
for summary in sorted(root.rglob('summary.json')):
    case=summary.parent.parent; s=read(summary); a=read(case/'analysis.json'); c=read(summary.parent/'metadata.json')['config']
    trace=[json.loads(x) for x in (summary.parent/'requests.jsonl').read_text().splitlines()]
    assert len({r['request_id'] for r in trace})==len(trace)
    assert a['evidence']['summary_counts_match_trace']
    counters=a['counter_deltas']; apis=[v for k,v in counters.items() if k.startswith('api')]; b=counters['backend']
    assert sum(v['requests'] for v in apis)==s['sent']
    assert sum(v['rejected'] for v in apis)==s['http_429']
    assert b['arrivals']==s['backend_confirmed_arrivals']
    assert b['arrivals']==b['success']+b['overload']+b['canceled']
    duration=c['duration_ns']/1e9; start=epoch(s['started_at']); phases=[]
    boundaries=[(0,duration,'measurement')]
    if c['profile']=='burst':
        bs=c['burst_start_ns']/1e9; be=bs+c['burst_duration_ns']/1e9
        boundaries=[(0,bs,'pre'),(bs,be,'burst'),(be,duration,'post')]
    quality=[]
    wall_elapsed=epoch(s['ended_at'])-start; clock_delta=wall_elapsed-s['elapsed_seconds_including_drain']
    if abs(clock_delta)>.01: quality.append('clock_wall_monotonic_discontinuity')
    for lo,hi,phase in boundaries:
        for cls in ('legitimate','abusive'):
            expected=c['legitimate_rps'] if cls=='legitimate' else (c['burst_rps'] if phase=='burst' else c['rps']-c['legitimate_rps'])
            if expected==0: continue
            selected=[r for r in trace if r['client_class']==cls and lo-1e-6<=epoch(r['scheduled_at'])-start<hi-1e-6]
            sent=[r for r in selected if r.get('sent_at')]
            ontime=[r for r in trace if r['client_class']==cls and r.get('sent_at') and lo<=epoch(r['sent_at'])-start<hi]
            actual=len(ontime)/(hi-lo); lag=p95([r['schedule_lag_ms'] for r in selected]); interval=1000/expected
            valid=abs(actual/expected-1)<=.05 and lag is not None and lag<=min(10,interval)
            phases.append(dict(phase=phase,client_class=cls,target_rps=expected,scheduled=len(selected),sent=len(sent),sent_in_phase=len(ontime),phase_seconds=hi-lo,actual_rps=actual,p95_lag_ms=lag,send_interval_ms=interval,valid=valid))
            if not valid: quality.append('phase_fidelity:'+phase+'/'+cls)
    if s['generator_dropped'] or s['sent']!=s['scheduled']: quality.append('generator_drops')
    errors=sum(v['limiter_errors'] for v in apis)
    if errors: quality.append('healthy_limiter_errors')
    senttimes=[epoch(r['sent_at']) for r in trace if r.get('sent_at')]
    row=dict(cell=str(case.relative_to(root)),profile=c['profile'],mode=c['mode_label'],algorithm=c['algorithm_label'],offered_duration_seconds=duration,send_span_seconds=max(senttimes)-min(senttimes),drain_elapsed_seconds=s['elapsed_seconds_including_drain'],wall_elapsed_seconds=wall_elapsed,wall_minus_monotonic_seconds=clock_delta,scheduled=s['scheduled'],sent=s['sent'],offered_rps=s['sent']/duration,drops=s['generator_dropped'],p95_lag_ms=s['schedule_lag']['p95_ms'],http_2xx=s['http_2xx'],http_429=s['http_429'],http_5xx=s['http_5xx'],legitimate_successful=s['legitimate_successful'],legitimate_goodput_per_offered_second=s['legitimate_successful']/duration,legitimate_goodput_including_drain=s['legitimate_goodput_per_second'],legitimate_p95_ms=s['legitimate_success_latency']['p95_ms'],legitimate_p99_ms=s['legitimate_success_latency']['p99_ms'],backend_arrivals=b['arrivals'],backend_success=b['success'],backend_overload=b['overload'],backend_canceled=b['canceled'],limiter_errors=errors,fail_open=sum(v['fail_open'] for v in apis),fail_closed=sum(v['fail_closed'] for v in apis),oracle=a['oracle']['status'],oracle_violations=len(a['oracle'].get('violations',[])),quality_flags=';'.join(quality),phases=phases)
    rows.append(row)
out.mkdir(parents=True,exist_ok=True)
(out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n')
with (out/'runs.csv').open('w') as f:
    fields=[k for k in rows[0] if k!='phases']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows({k:r[k] for k in fields} for r in rows)
print(json.dumps([{k:r[k] for k in ('cell','drops','p95_lag_ms','backend_overload','legitimate_successful','limiter_errors','oracle','quality_flags')} for r in rows],indent=2))
