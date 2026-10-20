#!/usr/bin/env python3
"""Focused v1.1 plan self-check; creates no measurement artifacts."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V1 = ROOT / 'docs/experiments/protocol-v1/manifest.json'
MANIFEST = HERE / 'manifest.json'


def load(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f'duplicate JSON key: {key}')
            out[key] = value
        return out
    return json.loads(path.read_text(), object_pairs_hook=unique)


def check():
    old, m = load(V1), load(MANIFEST)
    assert m['protocol_id'] == 'project3-formal-v1.1'
    assert m['status'] in ('draft-pending-tooling-integration-and-live-smoke', 'locked')
    assert (m['status'] == 'draft-pending-tooling-integration-and-live-smoke' and m['execution_authorized'] in (False, True)) or (m['status'] == 'locked' and m['execution_authorized'] is True)
    assert m['source_revision'] == '0291a80fb404fea0eafee8c3431acc3631bb423e'
    assert len(m['cells']) == m['planned_cell_count'] == 46
    assert len(m['runs']) == m['planned_run_count'] == 138
    assert len(m['invocations']) == 132
    # Scientific matrix, order, configuration, and thresholds match the immutable v1 plan.
    for field in ('schema_version', 'clock_tolerance_ms', 'planned_repetitions', 'planned_duration_s'):
        assert m[field] == old[field]
    assert m['cells'] == old['cells']
    for field in ('normal_block_order', 'outage_block_order'):
        assert m['run_order'][field] == old['run_order'][field]
    assert m['recovery'] == old['recovery']
    assert m['network_metrics'] == old['network_metrics']
    assert m['atomicity_rq4'] == old['atomicity_rq4']
    assert [r['order'] for r in m['runs']] == list(range(1, 139))
    assert [r['cell'] for r in m['runs']] == [r['cell'] for r in old['runs']]
    assert [r['config'] for r in m['runs']] == [r['config'] for r in old['runs']]
    assert all(r['source_revision'] == m['source_revision'] for r in m['runs'])
    assert [r['repetition'] for r in m['runs']] == [r['repetition'] for r in old['runs']]
    assert len({r['planned_run_id'] for r in m['runs']}) == 138
    ids = {i['id']: i for i in m['invocations']}
    assert len(ids) == 132
    paths = [r['result_path'] for r in m['runs']]
    assert len(set(paths)) == len(paths)
    assert all(path.startswith('../../../../artifacts/protocol-v1.1/') for path in paths)
    assert all(not (ROOT / 'docs/experiments/protocol-v1.1/results' / path).resolve().exists() for path in paths), 'planned result path exists; preserve it and choose new output root before execution'
    # Standard invocations remain one row each; outage invocations pair only phases of one policy.
    standard = [r for r in m['runs'] if not r['cell'].startswith('outage-')]
    outage = [r for r in m['runs'] if r['cell'].startswith('outage-')]
    assert len(standard) == 126 and len({r['invocation_id'] for r in standard}) == 126
    assert len(outage) == 12 and len({r['invocation_id'] for r in outage}) == 6
    for r in m['runs']:
        inv = ids[r['invocation_id']]
        assert r['command'] == inv['command'] and r['environment'] == inv['environment']
        assert r['output_path'] == inv['output_path']
        assert r['planned_run_id'] in inv['planned_run_ids']
        assert r['output_path'].startswith('artifacts/protocol-v1.1/')
        if r in standard:
            assert len(inv['planned_run_ids']) == 1
            assert r['command'][:3] == ['bash', 'scripts/research-pilot.sh', '--output']
            assert r['command'][3] == r['output_path']
            assert r['result_path'] == f'../../../../{r["output_path"]}/custom-repeat-1'
        else:
            policy = 'open' if '-open-' in r['cell'] else 'closed'
            phase = 'healthy' if r['cell'].endswith('-healthy') else 'outage'
            assert inv['id'] == f'outage-{policy}-r{r["repetition"]}'
            assert len(inv['planned_run_ids']) == 2
            assert inv['command'][:3] == ['bash', 'scripts/redis-outage.sh', r['output_path']]
            assert inv['command'][3:5] == ['--policy', policy]
            assert inv['command'][5:7] == ['--quality-manifest', '<ABSOLUTE_PROTOCOL_V1_1_MANIFEST>']
            pair = [x for x in outage if x['invocation_id'] == inv['id']]
            assert {x['cell'] for x in pair} == {f'outage-{policy}-healthy', f'outage-{policy}-outage'}
            assert r['result_path'] == f'../../../../{r["output_path"]}/{policy}/{phase}'
            if phase == 'outage':
                threshold = '81.9048105' if policy == 'open' else '82.577208'
                assert r['fixed_analysis_commands'][-1] == ['timeout','20s','python3','scripts/analyze.py',f'{r["output_path"]}/{policy}/outage','--recovery-p95-ms',threshold,'--recovery-window-ms','1000','--recovery-min-samples','5','--recovery-consecutive','3']
    # Two replacement caps are global per cell/policy, with unique paths required for every attempt.
    assert 'two replacement attempts total per cell' in m['replacement_policy']['non_outage']
    assert 'two paired replacement attempts per policy' in m['replacement_policy']['outage']
    assert '.attempt-N' in m['attempt_paths']['replacement_template']
    for rep in ('1', '2', '3'):
        outage_ids = [r['cell'] for r in m['runs'] if r['repetition'] == rep and r['cell'].startswith('outage-')]
        assert outage_ids == ['outage-open-healthy','outage-open-outage','outage-closed-healthy','outage-closed-outage']
    print(f'PASS: v1.1 preserves v1 scientific matrix/order; 46 cells, 138 planned slots, 132 invocations; 126 standard + 6 policy outage pairs; source {m["source_revision"]}')


if __name__ == '__main__':
    try:
        check()
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
