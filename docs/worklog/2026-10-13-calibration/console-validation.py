import json, time, urllib.request, pathlib
out=pathlib.Path('artifacts/calibration-20261013/console-http');out.mkdir(exist_ok=True)
c=dict(mode='redis',algorithm='fixed-window',profile='normal',fail_policy='closed',instances=2,rps=20,legitimate_rps=20,duration_seconds=6,limit=20,window_ms=1000,capacity=20,refill_rate=20,backend_capacity=4,backend_service_ms=50,burst_start_seconds=1,burst_duration_seconds=1,burst_rps=200,concurrent_at_seconds=2,concurrent_count=100)
data=dict(case='custom',repetitions=2,mixed_rps=0,custom=c)
(out/'request.json').write_text(json.dumps(data,indent=2))
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8090'+path,timeout=10) as r:return json.load(r)
req=urllib.request.Request('http://127.0.0.1:8090/api/runs',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=10) as r:created=json.load(r)
(out/'created.json').write_text(json.dumps(created,indent=2));id=created['id']
for _ in range(150):
    result=get('/api/runs/'+id)
    if result['run']['state']!='running':break
    time.sleep(2)
(out/'completed.json').write_text(json.dumps(result,indent=2))
assert result['run']['state']=='completed',result
assert set(result['summaries'])==set(result['analyses'])=={'1','2'}
for i in ('1','2'):
    base=pathlib.Path('artifacts/console')/id/'result'/('custom-repeat-'+i)
    assert result['summaries'][i]==json.load(open(base/'load/summary.json'))
    assert result['analyses'][i]==json.load(open(base/'analysis.json'))
(out/'checks.txt').write_text('Both selected summary and analysis maps match raw repetitions 1 and 2. Completed with cleanup verified by controller.\n')
print(id)
