#!/usr/bin/env python3
"""Read-only continuation plan check; does not create measurement artifacts."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST = HERE / 'manifest.json'


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check():
    m = read_json(MANIFEST)
    continuation = m['continuation']
    source_manifest = (HERE / continuation['source_manifest_path']).resolve()
    source_ledger = Path(continuation['source_ledger_path'])
    assert sha256(source_manifest) == continuation['source_manifest_sha256']
    assert sha256(source_ledger) == continuation['source_ledger_sha256']
    old = read_json(source_manifest)

    assert m['protocol_id'] == 'project3-formal-v1.2'
    assert m['status'] == 'locked'
    assert m['execution_authorized'] is True
    assert m['source_revision'] == '0291a80fb404fea0eafee8c3431acc3631bb423e'
    assert m['source_revision'] == old['source_revision']
    assert m['planned_cell_count'] == old['planned_cell_count'] == len(m['cells']) == 46
    assert m['planned_run_count'] == old['planned_run_count'] == len(m['runs']) == 138
    assert len(m['invocations']) == 132
    for key in ('schema_version', 'clock_tolerance_ms', 'planned_repetitions', 'planned_duration_s',
                'planned_cell_count', 'planned_run_count', 'cells', 'recovery', 'network_metrics', 'atomicity_rq4'):
        assert m[key] == old[key], f'v1.1 scientific field changed: {key}'
    for key in ('normal_block_order', 'outage_block_order'):
        assert m['run_order'][key] == old['run_order'][key]
    for new, prior in zip(m['runs'], old['runs']):
        for key in ('planned_run_id', 'cell', 'group', 'repetition', 'order', 'source_revision', 'config'):
            assert new[key] == prior[key], f'planned run changed {key}: {new.get("planned_run_id")}'
    assert {r['planned_run_id'] for r in m['runs']} == {r['planned_run_id'] for r in old['runs']}

    assert m['validation_tool']['revision'] == '371ed1184800d81791821ab6b048243d6510fbcb'
    assert m['validation_tool']['checker_revision'] == m['validation_tool']['revision']
    assert m['validation_tool']['checker_fix_commit'] == 'd28fc927bade1dd7bedb832e80d7ab8645908529'
    assert m['validation_tool']['checker_sha256'] == 'fe4687d79b738e2715ef5f650bb9b6597641b990bcd5d3b1dd5852af1f90aae4'
    assert m['validation_tool']['coordinator_sha256'] == 'c20dbab7c5f4c1a318141123ef07f596a435f370c9b3686f3341797bfd111a8a'
    assert m['validation_tool']['measurement_source_revision'] == m['source_revision']
    assert m['continuation_driver']['stage_b_resume_command'].find('--resume-imported') >= 0
    assert m['continuation_state']['diagnostic_prelock_import']['accepted_slots'] == 104
    assert m['continuation_state']['diagnostic_prelock_import']['remaining_missing_slots'] == 34
    assert m['continuation_state']['diagnostic_prelock_import']['status'].startswith('diagnostic only')
    assert 'fresh Stage A import' in m['continuation_state']['official_import_gate']
    assert m['retry_policy'] == {'scope':'planned_invocation','max_new_attempts':3,'legacy_attempts_preserved':True}
    assert m['replacement_policy']['max_new_attempts'] == 3
    assert m['run_order']['budget']['historical_v1_1_max_offered_load_seconds_with_replacements'] == 6900
    assert 'two total replacement attempts per non-outage cell' in m['run_order']['budget']['historical_v1_1_replacement_policy']
    assert 'at most three new v1.2 attempts' in m['run_order']['replacement_limit']

    invocation = {x['id']: x for x in m['invocations']}
    assert len(invocation) == 132
    assert len({x['output_path'] for x in m['invocations']}) == 132
    assert all(x['output_path'].startswith('artifacts/protocol-v1.2/') for x in m['invocations'])
    assert all(not (ROOT / x['output_path']).exists() for x in m['invocations']), 'planned output root exists; use a fresh root without overwriting it'
    assert len({r['planned_run_id'] for r in m['runs']}) == 138
    paths = [r['result_path'] for r in m['runs']]
    assert len(paths) == len(set(paths))
    assert all(p.startswith('../../../../artifacts/protocol-v1.2/') for p in paths)
    assert all('protocol-v1.1' not in p for p in paths)
    assert all('<ABSOLUTE_PROTOCOL_V1_1_MANIFEST>' not in json.dumps(x) for x in m['runs'] + m['invocations'])
    assert all(not (ROOT / 'docs/experiments/protocol-v1.2/results' / p).resolve().exists()
               for p in paths), 'planned v1.2 output exists; select a fresh root without overwriting it'
    standard = [r for r in m['runs'] if not r['cell'].startswith('outage-')]
    outage = [r for r in m['runs'] if r['cell'].startswith('outage-')]
    assert len(standard) == 126 and len({r['invocation_id'] for r in standard}) == 126
    assert len(outage) == 12 and len({r['invocation_id'] for r in outage}) == 6
    for r in m['runs']:
        inv = invocation[r['invocation_id']]
        assert r['source_revision'] == m['source_revision']
        assert r['output_path'].startswith('artifacts/protocol-v1.2/')
        assert 'artifacts/protocol-v1.2/' in r['result_path']
        assert r['planned_run_id'] in inv['planned_run_ids']
        assert r['command'] == inv['command'] and r['environment'] == inv['environment']
        assert r['output_path'] == inv['output_path']
        if r in standard:
            assert len(inv['planned_run_ids']) == 1
            assert r['command'][0:3] == ['bash','scripts/research-pilot.sh','--output']
            assert r['command'][3] == r['output_path']
        else:
            policy = 'open' if '-open-' in r['cell'] else 'closed'
            phase = 'healthy' if r['cell'].endswith('-healthy') else 'outage'
            assert inv['id'] == f'outage-{policy}-r{r["repetition"]}'
            assert len(inv['planned_run_ids']) == 2
            assert inv['command'][0:3] == ['bash','scripts/redis-outage.sh',r['output_path']]
            assert inv['command'][3:5] == ['--policy',policy]
            assert inv['command'][5:7] == ['--quality-manifest','<ABSOLUTE_PROTOCOL_V1_2_MANIFEST>']
            assert r['result_path'].endswith(f'/{policy}/{phase}')
            if phase == 'outage':
                threshold = '81.9048105' if policy == 'open' else '82.577208'
                assert r['fixed_analysis_commands'][-1][r['fixed_analysis_commands'][-1].index('--recovery-p95-ms')+1] == threshold
    assert m['runtime']['redis_image'] == old['runtime']['redis_image']
    assert m['runtime']['nginx_image'] == old['runtime']['nginx_image']
    assert m['continuation_state']['ledger_state_before_corrected_offline_revalidation']['unfinished_invocation'] == 'p1-108-mixed-redis-fw-r3'
    assert 'Do not choose by measured performance' in m['continuation_state']['reclaim_rule']
    assert m['continuation']['source_manifest_sha256'] == '32f8c6eb34bfd17e45b5dab5e1411b04ce410cf4b49c9ed495678fcb47fb3f79'
    assert m['continuation']['source_ledger_sha256'] == 'bd6c89ce44907d1d8ec72a7f7fe4c0cca03f0afaaf34b2347deab43fa2c29a16'
    print(f'PASS: locked v1.2 preserves v1.1 science and all 138 planned IDs; 132 invocations; source {m["source_revision"]}; tool {m["validation_tool"]["revision"]}; official import required before new load')


if __name__ == '__main__':
    try:
        check()
    except (AssertionError, KeyError, OSError, TypeError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
