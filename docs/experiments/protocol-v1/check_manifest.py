#!/usr/bin/env python3
"""Focused structural and existing-runner adapter check for the locked T08 plan."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name('manifest.json')
REV = 'b090d2b7391db873a0a2bbe602321ed1f5a55691'


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load():
    return json.loads(MANIFEST.read_text(), object_pairs_hook=no_duplicate_keys)


def check():
    m = load()
    assert m['schema_version'] == 1 and m['protocol_id'] == 'project3-formal-v1'
    assert m['status'] == 'locked' and m['execution_authorized'] is False
    assert m['source_revision'] == REV
    cells, runs = m['cells'], m['runs']
    assert len(cells) == m['planned_cell_count'] == 46
    assert len(runs) == m['planned_run_count'] == 138
    assert len({c['id'] for c in cells}) == len(cells)
    assert [r['order'] for r in runs] == list(range(1, 139))
    assert all(r['source_revision'] == REV for r in runs)
    assert all('TODO' not in json.dumps(x) and 'pending-integration' not in json.dumps(x) for x in (m,))

    expected_blocks = {'normal': 5, 'burst': 5, 'mixed': 5, 'scaling': 27, 'outage': 4}
    assert {name: sum(c['block'] == name for c in cells) for name in expected_blocks} == expected_blocks
    cell_by_id = {c['id']: c for c in cells}
    assert {c['expected_repetitions'] for c in cells} == {3}
    assert len({r['planned_run_id'] for r in runs}) == len(runs)
    paths = [r['result_path'] for r in runs]
    assert len(set(paths)) == len(paths)
    assert all(not (ROOT / 'docs/experiments/protocol-v1/results' / p).resolve().exists() for p in paths), 'planned result path already exists; preserve plan and choose new results root before execution'

    non_outage = [c for c in cells if c['block'] != 'outage']
    expected_order = sorted(non_outage, key=lambda c: hashlib.sha256(('project3-t08-protocol-v1:' + c['id']).encode()).hexdigest())
    expected_ids = [c['id'] for c in expected_order]
    for rep in ('1', '2', '3'):
        block_runs = [r for r in runs if r['repetition'] == rep]
        assert [r['cell'] for r in block_runs[:42]] == expected_ids
        assert [r['cell'] for r in block_runs[42:]] == ['outage-open-healthy', 'outage-open-outage', 'outage-closed-healthy', 'outage-closed-outage']
    for c in cells:
        selected = [r for r in runs if r['cell'] == c['id']]
        assert len(selected) == 3 and {r['repetition'] for r in selected} == {'1', '2', '3'}
        for r in selected:
            assert r['config'] == {k: c[k] for k in ('workload', 'policy', 'topology')}
            assert r['group'] == '+'.join(c['rqs'])

    invocations = {i['id']: i for i in m['invocations']}
    assert len(invocations) == 129
    assert len({r['invocation_id'] for r in runs if cell_by_id[r['cell']]['block'] != 'outage'}) == 126
    for r in runs:
        c = cell_by_id[r['cell']]
        inv = invocations[r['invocation_id']]
        assert r['environment'] == inv['environment'] and r['command'] == inv['command']
        assert r['output_path'] == inv['output_path']
        assert r['planned_run_id'] in inv['planned_run_ids']
        if c['block'] != 'outage':
            w, p, t = c['workload'], c['policy'], c['topology']
            env = r['environment']
            assert r['command'] == ['bash', 'scripts/research-pilot.sh', '--output', r['output_path'], '--case', 'custom', '--repetitions', '1', '--analyze', '--host-port', '18080']
            expected_env = {'CUSTOM_MODE':p['mode'],'CUSTOM_ALGORITHM':p['algorithm'],'CUSTOM_INSTANCES':str(t['api_instances']),
                'CUSTOM_PROFILE':w['profile'],'CUSTOM_RPS':str(w['rps']),'CUSTOM_LEGIT_RPS':str(w['legitimate_rps']),
                'CUSTOM_DURATION':'30','CUSTOM_LIMIT':str(p['limit']),'CUSTOM_WINDOW_MS':str(p['window_ms']),
                'CUSTOM_CAPACITY':str(p['capacity']),'CUSTOM_RATE':str(p['rate_per_sec']),
                'CUSTOM_BACKEND_CAPACITY':str(t['backend_capacity']),'CUSTOM_BACKEND_SERVICE_MS':str(t['backend_service_ms']),
                'CUSTOM_FAIL_POLICY':p['fail_policy'],'CUSTOM_BURST_START':'2','CUSTOM_BURST_DURATION':'2','CUSTOM_BURST_RPS':'200','LAB_HOST_PORT':'18080'}
            assert env == expected_env
            assert r['result_path'] == '../../../../' + r['output_path'] + '/custom-repeat-1'
            assert r['runner_run_id_pattern'] == 'custom-repeat-1'
            assert 1 <= int(env['CUSTOM_RPS']) <= 1000 and 3 <= int(env['CUSTOM_DURATION']) <= 30
            assert int(env['CUSTOM_INSTANCES']) in (1, 2, 4)
        else:
            assert r['command'] == ['bash','scripts/redis-outage.sh',r['output_path']]
            assert r['environment'] == {'OUTAGE_DURATION':'30','OUTAGE_RPS':'100','OUTAGE_LEGIT_RPS':'20','OUTAGE_PAUSE_AT':'4','OUTAGE_PAUSE_FOR':'2','OUTAGE_HOST_PORT':'18080','ALGORITHM':'fixed-window','LIMIT':'20','WINDOW':'1s','CAPACITY':'20','RATE':'20','BACKEND_CAPACITY':'10','BACKEND_SERVICE_TIME':'50ms'}
            policy = c['policy']['fail_policy']
            phase = 'healthy' if c['id'].endswith('-healthy') else 'outage'
            assert r['result_path'] == f'../../../../{r["output_path"]}/{policy}/{phase}'
            assert r['runner_run_id_pattern'] == 't07-<UTC timestamp>-<PID>-<policy>-<phase>'
            if phase == 'outage':
                threshold = '81.9048105' if policy == 'open' else '82.577208'
                commands = r['fixed_analysis_commands']
                assert commands[-1] == ['timeout','20s','python3','scripts/analyze.py',f'{r["output_path"]}/{policy}/outage','--recovery-p95-ms',threshold,'--recovery-window-ms','1000','--recovery-min-samples','5','--recovery-consecutive','3']

    # Adapter names and core flags are checked against the existing implementation, not a copy of its algorithms.
    runner = (ROOT / 'scripts/research-pilot.sh').read_text()
    outage = (ROOT / 'scripts/redis-outage.sh').read_text()
    assert all(x in runner for x in ('CUSTOM_MODE','CUSTOM_ALGORITHM','CUSTOM_INSTANCES','CUSTOM_PROFILE','CUSTOM_RPS','CUSTOM_LEGIT_RPS','CUSTOM_DURATION','CUSTOM_BACKEND_CAPACITY','CUSTOM_BACKEND_SERVICE_MS','--analyze'))
    assert all(x in outage for x in ('OUTAGE_DURATION','OUTAGE_RPS','OUTAGE_LEGIT_RPS','OUTAGE_PAUSE_AT','OUTAGE_PAUSE_FOR','recovery-p95-threshold-ms.txt','--recovery-p95-ms'))
    assert m['recovery']['frozen_p95_threshold_ms'] == {'open':81.9048105,'closed':82.577208}
    assert m['recovery']['window_ms'] == 1000 and m['recovery']['min_legitimate_samples'] == 5 and m['recovery']['consecutive_clean_windows'] == 3
    assert m['runtime']['redis_image']['configured_reference'] == 'redis:7.4.2-alpine'
    assert m['runtime']['redis_image']['inspected_id'] == m['runtime']['redis_image']['repo_digest'].replace('redis@', '')
    assert m['network_metrics']['fields'] == ['network_input_bytes_delta','network_input_bytes_per_second','network_output_bytes_delta','network_output_bytes_per_second']
    print(f'PASS: {len(cells)} cells, {len(runs)} planned slots, {len(invocations)} runner invocations; source {REV}')


if __name__ == '__main__':
    try:
        check()
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
