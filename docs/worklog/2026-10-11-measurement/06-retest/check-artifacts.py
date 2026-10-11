"""Validate recorded measurement pilots; report load-fidelity failures without hiding runs."""
import json
from pathlib import Path

reports = []
roots = ('measurement-pilot', 'measurement-resume-2', 'measurement-rerun', 'measurement-calibration')
for root in roots:
    for path in sorted((Path('artifacts') / root).glob('*/load/summary.json')):
        case = path.parent.parent
        summary = json.loads(path.read_text())
        analysis = json.loads((case / 'analysis.json').read_text())
        records = [json.loads(line) for line in (path.parent / 'requests.jsonl').read_text().splitlines()]
        assert len(records) == summary['scheduled']
        assert len({r['request_id'] for r in records}) == len(records)
        assert sum('sent_at' in r for r in records) == summary['sent']
        assert summary['sent'] + summary['generator_dropped'] == summary['scheduled']
        assert sum(r.get('backend_arrival') == 'true' for r in records) == analysis['counter_deltas']['backend']['arrivals']
        assert not analysis['oracle'].get('violations'), (case, analysis['oracle']['violations'])
        instances = 1 if case.name.startswith('scale-1') else 4 if case.name.startswith('scale-4') else 2
        assert len({r.get('instance') for r in records if 'sent_at' in r}) == instances
        config = json.loads((case / 'compose-resolved.json').read_text())
        assert len([k for k in config['services'] if k.startswith('api')]) == instances
        assert config['services']['backend']['environment']['BACKEND_CAPACITY'] == ('4' if root == 'measurement-calibration' else '10')
        assert config['services']['backend']['environment']['BACKEND_SERVICE_TIME'] == '50ms'
        checks = analysis['oracle'].get('trace_decision_checks', [])
        item = {'case': case.name, 'path': str(case), 'planned': summary['scheduled'],
                'backend_capacity': config['services']['backend']['environment']['BACKEND_CAPACITY'],
                'sent': summary['sent'], 'dropped': summary['generator_dropped'],
                'transport_errors': summary['transport_errors'], '2xx': summary['http_2xx'],
                '429': summary['http_429'], '5xx': summary['http_5xx'],
                'backend_arrivals': analysis['counter_deltas']['backend']['arrivals'],
                'goodput': summary['legitimate_goodput_per_second'],
                'lag_p99_ms': summary['schedule_lag']['p99_ms'], 'oracle': analysis['oracle']['status'],
                'checked_fw_groups': sum(c['status'] == 'checked' for c in checks),
                'fw_global_overshoot_lower_bound': sum(c.get('shared_quota_overshoot_lower_bound', 0)
                    for c in analysis['oracle'].get('observed_global_accepted_envelope', [])),
                'load_fidelity': 'no_drops_or_transport_errors' if summary['generator_dropped'] == 0 and summary['transport_errors'] == 0 else 'invalid_offered_load'}
        reports.append(item)
        print(json.dumps(item))
assert len({r['case'] for r in reports}) == 11
result = {'runs': reports, 'unique_cases': 11,
          'planned_all_attempts': sum(r['planned'] for r in reports),
          'sent_all_attempts': sum(r['sent'] for r in reports),
          'invalid_load_attempts': [r['path'] for r in reports if r['load_fidelity'] == 'invalid_offered_load']}
Path('docs/worklog/2026-10-11-measurement/06-retest/pilot-summary.json').write_text(json.dumps(result, indent=2)+'\n')
print('Artifact consistency PASS; inspect load_fidelity separately from quota checks.')
