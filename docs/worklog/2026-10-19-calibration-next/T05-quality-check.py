import datetime as dt, json, math, pathlib, sys
p=pathlib.Path(sys.argv[1]); s=json.loads((p/'load/summary.json').read_text()); meta=json.loads((p/'load/metadata.json').read_text()); c=meta['config']; a=json.loads((p/'analysis.json').read_text()); rows=[json.loads(x) for x in (p/'load/requests.jsonl').read_text().splitlines()]; flags=[]; target=c['rps']; duration=c['duration_ns']/1e9
cell=p.parent.name
parts=cell.split('-')
expected_mode=parts[0]; expected_instances=int(parts[2][3:]); expected_rps=int(parts[3][3:])
policy=json.loads((p/'policy.json').read_text()); compose=json.loads((p/'compose-resolved.json').read_text()); services=compose['services']
api_services=[name for name in services if name.startswith('api')]
if c['profile']!='normal' or c['algorithm_label']!='fixed-window' or c['mode_label']!=expected_mode or c['legitimate_rps']!=expected_rps or c['legitimate_clients']!=5 or duration!=10: flags.append('load_config')
if len(api_services)!=expected_instances: flags.append('topology_config')
if policy['mode']!=expected_mode or policy['algorithm']!='fixed-window' or policy['fail_policy']!='closed' or policy['limit']!=1000 or policy['capacity']!=1000 or policy['window_ms']!=1000 or policy['rate_per_sec']!=1000 or policy['state_reset'] is not True: flags.append('policy_config')
if services['backend']['environment'].get('BACKEND_CAPACITY')!='10' or services['backend']['environment'].get('BACKEND_SERVICE_TIME')!='50ms': flags.append('backend_config')
if meta['git_revision']!='26b5decb835dbb136eb2d45b361920a414434f6b' or meta['git_status_porcelain']!='': flags.append('revision_or_dirty_checkout')
if s['scheduled']!=target*duration or s['sent']!=s['scheduled'] or s['generator_dropped']!=0 or len(rows)!=s['scheduled'] or len({r['request_id'] for r in rows})!=len(rows): flags.append('schedule_or_drop_reconcile')
if not a['evidence']['summary_counts_match_trace']: flags.append('analyzer_summary_reconcile')
if any(r['client_class']!='legitimate' or r['phase']!='measurement' for r in rows): flags.append('class_or_phase')
actual=s['sent']/duration
if abs(actual/target-1)>.05: flags.append('offered_rate_fidelity')
lag=s['schedule_lag']['p95_ms']
if lag>min(10,1000/target): flags.append('schedule_lag')
start=dt.datetime.fromisoformat(s['started_at']); sent=[r for r in rows if r.get('sent_at')]
def epoch(t): return dt.datetime.fromisoformat(t).timestamp()
if not sent: flags.append('no_sent_records')
else:
 for r in sent:
  sr=abs((epoch(r['sent_at'])-epoch(r['scheduled_at']))*1000-r['schedule_lag_ms'])
  lr=abs((epoch(r['end_at'])-epoch(r['sent_at']))*1000-r['latency_ms'])
  if max(sr,lr)>5: flags.append('clock_residual'); break
api=[v for k,v in a['counter_deltas'].items() if k.startswith('api')]; b=a['counter_deltas']['backend']
if sum(x['requests'] for x in api)!=s['sent'] or sum(x['rejected'] for x in api)!=s['http_429'] or sum(x['backend_confirmed_arrivals'] for x in api)!=s['backend_confirmed_arrivals'] or b['arrivals']!=s['backend_confirmed_arrivals'] or b['arrivals']!=b['success']+b['overload']+b['canceled']: flags.append('counter_reconcile')
limerr=sum(x['limiter_errors'] for x in api)
if limerr: flags.append('healthy_redis_errors')
if s['http_429']: flags.append('quota_headroom')
if flags:
 result={'valid':False,'flags':sorted(set(flags)),'sent':s['sent'],'drops':s['generator_dropped']}
 (p/'t05-quality.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result)); sys.exit(1)
residuals=[abs((epoch(r['sent_at'])-epoch(r['scheduled_at']))*1000-r['schedule_lag_ms']) for r in sent]+[abs((epoch(r['end_at'])-epoch(r['sent_at']))*1000-r['latency_ms']) for r in sent]
result={'valid':True,'flags':[],'sent':s['sent'],'drops':s['generator_dropped'],'target_rps':target,'actual_rps':actual,'p95_schedule_lag_ms':lag,'clock_residual_max_ms':max(residuals,default=0),'http_429':s['http_429'],'limiter_errors':limerr,'backend_success':b['success'],'backend_overload':b['overload'],'legitimate_goodput_per_second':s['legitimate_goodput_per_second'],'legitimate_success_p95_ms':s['legitimate_success_latency']['p95_ms'],'oracle':a['oracle']['status']}
(p/'t05-quality.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
