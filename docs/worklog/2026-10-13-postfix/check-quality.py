import json, pathlib, datetime as dt, math, sys
case=pathlib.Path(sys.argv[1]);s=json.load(open(case/'load/summary.json'));a=json.load(open(case/'analysis.json'));c=json.load(open(case/'load/metadata.json'))['config'];trace=[json.loads(x) for x in open(case/'load/requests.jsonl')]
def epoch(t):return dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
flags=[];sent=[r for r in trace if r.get('sent_at')];residuals=[abs((epoch(r['sent_at'])-epoch(r['scheduled_at']))*1000-r['schedule_lag_ms']) for r in sent];latres=[abs((epoch(r['end_at'])-epoch(r['sent_at']))*1000-r['latency_ms']) for r in sent]
if max(residuals+latres)>5:flags.append('clock')
if s['generator_dropped']:flags.append('drops')
assert len({r['request_id'] for r in trace})==s['scheduled']==len(trace)
assert a['evidence']['summary_counts_match_trace']
assert s['sent']==s['scheduled']-s['generator_dropped']
api=[v for k,v in a['counter_deltas'].items() if k.startswith('api')];b=a['counter_deltas']['backend']
assert sum(x['requests'] for x in api)==s['sent'];assert sum(x['rejected'] for x in api)==s['http_429'];assert b['arrivals']==s['backend_confirmed_arrivals']==b['success']+b['overload']+b['canceled']
errors=sum(x['limiter_errors'] for x in api)
if errors:flags.append('healthy_redis_errors')
duration=c['duration_ns']/1e9;start=epoch(s['started_at']);fidelity=[]
for cls in ('legitimate','abusive'):
 target=c['legitimate_rps'] if cls=='legitimate' else c['rps']-c['legitimate_rps']
 if not target:continue
 selected=[r for r in sent if r['client_class']==cls];actual=sum(0<=epoch(r['sent_at'])-start<duration for r in selected)/duration;lag=sorted(r['schedule_lag_ms'] for r in selected)[math.ceil(.95*len(selected))-1]
 good=abs(actual/target-1)<=.05 and lag<=min(10,1000/target)
 if not good:flags.append('fidelity')
 fidelity.append(dict(client_class=cls,target_rps=target,actual_wall_phase_rps=actual,p95_lag_ms=lag,valid=good))
if c['profile']=='normal' and (s['http_429'] or b['overload']):flags.append('normal_outcome')
r=dict(case=str(case),profile=c['profile'],flags=sorted(set(flags)),valid=not flags,sent=s['sent'],drops=s['generator_dropped'],max_schedule_clock_residual_ms=max(residuals),max_latency_clock_residual_ms=max(latres),limiter_errors=errors,backend=b,oracle=a['oracle']['status'],summary=s,fidelity=fidelity)
(case/'quality.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('case','flags','valid','max_schedule_clock_residual_ms','max_latency_clock_residual_ms','limiter_errors')}))
