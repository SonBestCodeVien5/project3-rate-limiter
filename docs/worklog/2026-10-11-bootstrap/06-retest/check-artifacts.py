import json, pathlib, collections
for root in ['artifacts/bootstrap-pilot','artifacts/bootstrap-outage']:
    for f in sorted(pathlib.Path(root).glob('*/load/summary.json')):
        case=f.parent.parent
        s=json.loads(f.read_text())
        records=[json.loads(x) for x in (f.parent/'requests.jsonl').read_text().splitlines()]
        assert len(records)==s['scheduled']
        assert len({r['request_id'] for r in records})==len(records)
        assert s['sent']+s['generator_dropped']==s['scheduled']
        assert s['generator_dropped']==0 and s['transport_errors']==0
        assert sum(r['status']==200 for r in records)==s['http_2xx']
        assert sum(r['status']==429 for r in records)==s['http_429']
        assert sum(r['status']>=500 for r in records)==s['http_5xx']
        assert all(r['backend_arrival']=='false' for r in records if r.get('limiter_decision') in ('reject','fail-closed'))
        before=json.loads((case/'backend-before.json').read_text())
        after=json.loads((case/'backend-after.json').read_text())
        assert after['arrivals']-before['arrivals']==s['backend_confirmed_arrivals']
        instances=collections.Counter(r['instance'] for r in records)
        assert set(instances)=={'api-1','api-2'}
        if 'outage' in root:
            expected='fail-'+case.name
            assert s['decisions'].get(expected,0)>0
            events=(case/'outage-events.txt').read_text()
            assert 'pause_completed' in events and 'unpause_completed' in events
            # Final requests regain ordinary decisions; this is recovery observation, not a recovery SLO.
            tail=sorted(records,key=lambda r:r['sent_at'])[-50:]
            assert all(r['limiter_decision'] in ('allow','reject') for r in tail)
        print(case, 'PASS', json.dumps({k:s[k] for k in ['scheduled','sent','generator_dropped','http_2xx','http_429','http_5xx','backend_confirmed_arrivals','legitimate_goodput_per_second','decisions']}), 'instances='+str(dict(instances)))
