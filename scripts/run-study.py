#!/usr/bin/env python3
"""Run the locked manifest sequentially and retain every attempt."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts/check-study-quality.py'


def now():
    return datetime.now(timezone.utc).isoformat()


def suspend_gap_ms():
    # shortcut: detects only guest-accounted suspend; use a host-side observer if WSL pauses can be hidden from Linux clocks.
    clock = getattr(time, 'CLOCK_BOOTTIME', None)
    if clock is None or not hasattr(time, 'CLOCK_MONOTONIC'):
        return None
    try:
        return (time.clock_gettime_ns(clock) - time.clock_gettime_ns(time.CLOCK_MONOTONIC)) / 1_000_000
    except OSError:
        return None


def groups(runs):
    ordered, indexed = [], {}
    for entry in runs:
        key = entry['invocation_id']
        if key not in indexed:
            indexed[key] = []
            ordered.append(indexed[key])
        indexed[key].append(entry)
    for group in ordered:
        if len(group) not in (1, 2) or (len(group) == 2 and (
                group[0]['cell'].rsplit('-', 1)[0] != group[1]['cell'].rsplit('-', 1)[0] or
                {entry['cell'].rsplit('-', 1)[-1] for entry in group} != {'healthy', 'outage'} or
                group[0]['config']['policy']['fail_policy'] != group[1]['config']['policy']['fail_policy'] or
                group[0]['command'] != group[1]['command'] or group[0]['output_path'] != group[1]['output_path'] or
                group[0]['environment'] != group[1]['environment'])):
            raise ValueError(f"invalid invocation group {group[0]['invocation_id']}")
    return ordered


def base_path(manifest_path, entry, measurement_root=ROOT):
    output = Path(entry['output_path'])
    result = Path(entry['result_path'])
    if output.is_absolute():
        try:
            return result.resolve() if result.is_absolute() else (measurement_root / output / result).resolve()
        except OSError:
            pass
    marker = str(output).rstrip('/')
    raw = str(result)
    if marker not in raw:
        raise ValueError(f"result_path does not identify output_path for {entry['planned_run_id']}")
    suffix = raw.split(marker, 1)[1].lstrip('/')
    return (measurement_root / output / suffix).resolve()


def sha256(path):
    import hashlib
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def tree_checksums(path):
    return {str(item.relative_to(path)): sha256(item) for item in sorted(path.rglob('*')) if item.is_file()}


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def docker_snapshot(measurement_root=ROOT):
    output = subprocess.check_output(['docker', 'ps', '-aq'], cwd=measurement_root, text=True)
    ids = output.split()
    if not ids:
        return set()
    details = json.loads(subprocess.check_output(['docker', 'inspect', *ids], cwd=measurement_root, text=True))
    return {item['Id'] for item in details if item.get('Config', {}).get('Labels', {}).get('com.docker.compose.project', '').startswith(('project3-research-lab', 'project3-outage-'))}


def preflight(manifest, manifest_path, observer_dir, measurement_root=ROOT):
    if manifest.get('execution_authorized') is not True or manifest.get('status') != 'locked':
        raise ValueError('manifest is a draft or execution is not authorized')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=measurement_root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=measurement_root, text=True)
    if revision != manifest['source_revision'] or dirty.strip():
        raise ValueError('measurement checkout must be clean at the manifest source_revision')
    for key in ('redis_image', 'nginx_image'):
        expected = manifest['runtime'][key]
        inspect = json.loads(subprocess.check_output(['docker', 'image', 'inspect', expected['configured_reference']], cwd=measurement_root, text=True))[0]
        if inspect.get('Id') != expected['inspected_id'] or expected['repo_digest'] not in inspect.get('RepoDigests', []):
            raise ValueError(f'pinned local base image mismatch: {key}')
    before = docker_snapshot(measurement_root)
    result = subprocess.run([sys.executable, str(measurement_root / 'scripts/observe-clock.py'), '--output', str(observer_dir), '--duration-seconds', '90'], cwd=measurement_root, check=False)
    if result.returncode:
        raise ValueError('fresh 90-second clock observer failed')
    summary = json.loads((observer_dir / 'summary.json').read_text())
    if summary.get('duration_seconds') != 90 or summary.get('elapsed_monotonic_seconds', 0) < 89.9 or summary.get('clock_steps_above_5ms'):
        raise ValueError('fresh 90-second observer did not pass the clock gate')
    return {'containers': before, 'summary': summary}


def check_cleanup(before, measurement_root=ROOT):
    leaked = docker_snapshot(measurement_root) - before
    if leaked:
        raise RuntimeError('runner left Compose containers behind: ' + ','.join(sorted(leaked)))


def checker_call(manifest_path, entry, run_dir, checker=CHECKER, measurement_root=ROOT, quality_path=None):
    quality = quality_path or (run_dir / 'coordinator-quality-check.json')
    check = subprocess.run([sys.executable, str(checker), '--manifest', str(manifest_path), '--planned-run-id', entry['planned_run_id'], '--run-dir', str(run_dir), '--output', str(quality)], cwd=measurement_root, check=False)
    decision = {'exit_code': check.returncode, 'stop_sequence': check.returncode == 2}
    if quality.exists():
        decision.update(json.loads(quality.read_text()))
    return decision


def fixed_outage_analysis(manifest_path, group, run_output, measurement_root=ROOT):
    policy = group[0]['config']['policy']['fail_policy']
    dynamic = run_output / policy / 'recovery-p95-threshold-ms.txt'
    if dynamic.exists():
        import shutil
        shutil.copy2(dynamic, dynamic.with_name('recovery-p95-threshold-ms.dynamic-t07.txt'))
    else:
        raise ValueError('dynamic T07 threshold evidence is missing')
    completed = []
    thresholds = {}
    for entry in group:
        for command in entry.get('fixed_analysis_commands', []):
            def rooted(token):
                original = entry['output_path']
                if token == original:
                    return str(run_output)
                if token.startswith(original.rstrip('/') + '/'):
                    return str(run_output / token[len(original.rstrip('/')) + 1:])
                return token
            actual = [rooted(token) for token in command]
            if len(actual) == 4 and actual[0] == 'cp' and actual[2].endswith(('analysis.json', 'analysis.md', 'analyzer.log')):
                source = Path(actual[2])
                if not source.is_absolute():
                    source = measurement_root / source
                destination = Path(actual[3])
                if not destination.is_absolute():
                    destination = measurement_root / destination
                destination.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(['cp', '-p', str(source), str(destination)], cwd=measurement_root, check=True)
                completed.append(actual)
            else:
                subprocess.run(actual, cwd=measurement_root, check=True)
                completed.append(actual)
                if '--recovery-p95-ms' in actual:
                    threshold = actual[actual.index('--recovery-p95-ms') + 1]
                    phase = Path(actual[actual.index('scripts/analyze.py') + 1])
                    phase = phase if phase.is_absolute() else measurement_root / phase
                    (phase / 'fixed-recovery-p95-threshold-ms.txt').write_text(threshold + '\n')
                    thresholds[str(phase)] = threshold
    return {'commands': completed, 'thresholds': thresholds}


FATAL_DRIFT_REASONS = ('revision_mismatch', 'dirty_checkout', 'pinned_compose_image_mismatch',
                       'pinned_base_image_mismatch', 'image_inspect_mismatch',
                       'policy_mismatch:', 'workload_config_mismatch:', 'topology_mismatch',
                       'backend_config_mismatch', 'topology_policy_mismatch:',
                       'topology_policy_evidence_mismatch', 'namespace_mismatch:',
                       'revision_evidence_missing')


def import_legacy(manifest, manifest_path, output, measurement_root=ROOT,
                  checker=CHECKER, validation_tool_sha256=None):
    """Revalidate immutable v1.1 attempts into a fresh v1.2 continuation output."""
    continuation = manifest['continuation']
    checker_sha256 = sha256(checker)
    coordinator_sha256 = validation_tool_sha256 or sha256(Path(__file__))
    tool_pin = manifest.get('validation_tool', {})
    if (tool_pin.get('measurement_source_revision')
            and tool_pin['measurement_source_revision'] != manifest.get('source_revision')):
        raise ValueError('validation-tool measurement source revision mismatch')
    if tool_pin.get('checker_sha256') and tool_pin['checker_sha256'] != checker_sha256:
        raise ValueError('validation checker checksum differs from manifest pin')
    if tool_pin.get('coordinator_sha256') and tool_pin['coordinator_sha256'] != coordinator_sha256:
        raise ValueError('validation coordinator checksum differs from manifest pin')
    source_manifest_path = (manifest_path.parent / continuation['source_manifest_path']).resolve()
    source_ledger = Path(continuation['source_ledger_path']).resolve()
    expected_manifest_sha = continuation['source_manifest_sha256']
    expected_ledger_sha = continuation['source_ledger_sha256']
    if sha256(source_manifest_path) != expected_manifest_sha:
        raise ValueError('legacy source manifest checksum mismatch')
    if sha256(source_ledger) != expected_ledger_sha:
        raise ValueError('legacy source ledger checksum mismatch')
    source_manifest = json.loads(source_manifest_path.read_text())
    if source_manifest.get('source_revision') != manifest.get('source_revision'):
        raise ValueError('legacy source revision differs from continuation pin')
    old_runs = {item['planned_run_id']: item for item in source_manifest['runs']}
    groups(source_manifest['runs'])
    new_runs = {item['planned_run_id']: item for item in manifest['runs']}
    if set(old_runs) != set(new_runs):
        raise ValueError('continuation planned IDs differ from source manifest')
    groups(manifest['runs'])
    for run_id, old in old_runs.items():
        new = new_runs[run_id]
        if (old['config'] != new['config'] or old['source_revision'] != new['source_revision']
                or old['environment'] != new['environment'] or old['invocation_id'] != new['invocation_id']):
            raise ValueError(f'continuation config, environment, invocation, or revision changed: {run_id}')

    records = [json.loads(line) for line in source_ledger.read_text().splitlines() if line]
    groups_by_attempt = {}
    expected_by_id = old_runs
    for row in records:
        ids = row.get('planned_run_ids')
        if not ids or row.get('source_revision') != source_manifest['source_revision']:
            raise ValueError('legacy ledger has missing IDs or source revision drift')
        if row.get('config') != [expected_by_id[run_id]['config'] for run_id in ids]:
            raise ValueError('legacy ledger config drift')
        if row.get('manifest_sha256') != expected_manifest_sha:
            raise ValueError('legacy ledger manifest checksum provenance mismatch')
        if any(run_id not in expected_by_id or expected_by_id[run_id]['invocation_id'] != row.get('invocation_id') for run_id in ids):
            raise ValueError('legacy ledger invocation mapping drift')
        expected_env = expected_by_id[ids[0]]['environment']
        if any(expected_by_id[run_id]['environment'] != expected_env for run_id in ids) or row.get('environment') != expected_env:
            raise ValueError('legacy ledger environment drift')
        if row.get('event') == 'attempt_finished':
            key = (row['invocation_id'], row['attempt'])
            if key in groups_by_attempt:
                raise ValueError('duplicate legacy finished attempt')
            groups_by_attempt[key] = row
            for run_id in ids:
                if run_id not in old_runs or old_runs[run_id]['invocation_id'] != row['invocation_id']:
                    raise ValueError('legacy attempt invocation mapping drift')
            if row.get('accepted'):
                if set(row.get('accepted_result_paths', {})) != set(ids):
                    raise ValueError('legacy accepted result mapping is incomplete')
                for run_id, path in row.get('accepted_result_paths', {}).items():
                    expected_checksums = row.get('evidence_checksums', {}).get(run_id)
                    if run_id not in ids or not expected_checksums or tree_checksums(Path(path)) != expected_checksums:
                        raise ValueError(f'legacy accepted raw checksum mismatch: {run_id}')

    output = Path(output).resolve()
    try:
        output.relative_to(measurement_root.resolve())
        raise ValueError('import output must be outside the measurement checkout')
    except ValueError as exc:
        if str(exc).startswith('import output'):
            raise
    if output == source_ledger.parent or source_ledger.is_relative_to(output):
        raise ValueError('import output would overlap legacy ledger')
    if output.exists() and any(output.iterdir()):
        raise ValueError('import output must be fresh and empty')
    output.mkdir(parents=True, exist_ok=True)
    validation_root = output / 'validations'
    accepted, fingerprints, accepted_evidence = {}, {}, {}
    audit = output / 'import-attempts.jsonl'
    for row in records:
        if row.get('event') != 'attempt_finished':
            continue
        ids = row['planned_run_ids']
        checks = {}
        selected_paths = {}
        for run_id in ids:
            entry = old_runs[run_id]
            if run_id in row.get('accepted_result_paths', {}):
                run_dir = Path(row['accepted_result_paths'][run_id]).resolve()
            else:
                planned_dir = base_path(source_manifest_path, entry, measurement_root)
                planned_output = Path(entry['output_path'])
                planned_output = planned_output if planned_output.is_absolute() else measurement_root / planned_output
                try:
                    suffix = planned_dir.relative_to(planned_output.resolve())
                except ValueError:
                    suffix = Path()
                attempt_root = Path(row['run_path'])
                if not attempt_root.is_absolute():
                    attempt_root = measurement_root / attempt_root
                run_dir = (attempt_root / suffix).resolve()
            selected_paths[run_id] = run_dir
            validation_file = validation_root / f'{row["invocation_id"]}-attempt-{row["attempt"]}' / f'{run_id}.json'
            validation_file.parent.mkdir(parents=True, exist_ok=True)
            decision = checker_call(source_manifest_path, entry, run_dir, checker,
                                    measurement_root, validation_file)
            reasons = decision.get('reasons', [])
            drift = [reason for reason in reasons if any(reason.startswith(prefix) for prefix in FATAL_DRIFT_REASONS)]
            if drift:
                raise ValueError(f'legacy actual config/image/revision drift for {run_id}: {drift}')
            checks[run_id] = {**decision, 'validation_path': str(validation_file),
                              'validation_sha256': sha256(validation_file) if validation_file.exists() else None,
                              'raw_checksums': tree_checksums(run_dir) if run_dir.exists() else {}}
        valid = len(checks) == len(ids) and all(c.get('valid') for c in checks.values())
        selected = valid and not any(run_id in accepted for run_id in ids)
        fingerprint_mismatch = False
        if selected:
            for run_id, decision in checks.items():
                cell = old_runs[run_id]['cell']
                fingerprint = (decision.get('config_fingerprint'), decision.get('image_fingerprint'))
                if cell in fingerprints and fingerprints[cell] != fingerprint:
                    valid = False
                    fingerprint_mismatch = True
                    decision.setdefault('reasons', []).append('import_same_cell_fingerprint_mismatch')
            selected = valid
            if selected:
                for run_id, path in selected_paths.items():
                    accepted[run_id] = str(path)
                    decision = checks[run_id]
                    accepted_evidence[run_id] = {
                        'raw_checksums': decision['raw_checksums'],
                        'config_fingerprint': decision.get('config_fingerprint'),
                        'image_fingerprint': decision.get('image_fingerprint')}
                for run_id, decision in checks.items():
                    fingerprints.setdefault(old_runs[run_id]['cell'],
                                            (decision.get('config_fingerprint'), decision.get('image_fingerprint')))
        old_checks = row.get('checks', {})
        if selected:
            import_reason = 'selected_earliest_valid_attempt'
        elif valid and any(run_id in accepted for run_id in ids):
            import_reason = 'later_valid_duplicate_not_selected'
        elif fingerprint_mismatch:
            import_reason = 'fingerprint_mismatch'
        else:
            import_reason = 'revalidation_failed'
        imported = {'event': 'legacy_attempt_revalidated', 'source_ledger_sha256': expected_ledger_sha,
                    'source_manifest_sha256': expected_manifest_sha, 'source_invocation_id': row['invocation_id'],
                    'planned_run_ids': ids, 'attempt': row['attempt'], 'source_revision': row['source_revision'],
                    'config': row['config'], 'environment': row.get('environment'),
                    'old_decision': {'accepted': row.get('accepted'), 'checks': old_checks,
                                     'setup_error': row.get('setup_error'), 'cleanup_error': row.get('cleanup_error')},
                    'new_decision': {'valid': valid, 'selected': selected, 'reason': import_reason,
                                     'checks': checks},
                    'source_run_paths': {run_id: str(selected_paths[run_id]) for run_id in ids},
                    'accepted_result_paths': {run_id: accepted[run_id] for run_id in ids} if selected else {},
                    'validation_tool': {'checker_sha256': checker_sha256,
                                        'coordinator_sha256': coordinator_sha256,
                                        'revision': tool_pin.get('revision')},
                    'raw_checksums': {run_id: checks[run_id]['raw_checksums'] for run_id in ids}}
        with audit.open('a') as stream:
            stream.write(json.dumps(imported, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
    results = {'schema_version': 1, 'protocol_id': manifest.get('protocol_id'),
               'manifest_sha256': sha256(manifest_path),
               'source_revision': manifest['source_revision'],
               'source_manifest_sha256': expected_manifest_sha, 'source_ledger_sha256': expected_ledger_sha,
               'validation_tool': {'checker_sha256': checker_sha256,
                                   'coordinator_sha256': coordinator_sha256,
                                   'revision': tool_pin.get('revision')},
               'accepted_evidence': accepted_evidence,
               'cells': [{'id': cell['id'], 'expected_repetitions': cell['expected_repetitions']}
                         for cell in manifest['cells']],
               'runs': [{'planned_run_id': entry['planned_run_id'], 'group': entry['group'], 'cell': entry['cell'],
                         'repetition': entry['repetition'], 'path': accepted[entry['planned_run_id']]}
                        for entry in manifest['runs'] if entry['planned_run_id'] in accepted],
               'missing_planned_run_ids': [entry['planned_run_id'] for entry in manifest['runs']
                                           if entry['planned_run_id'] not in accepted]}
    imported_manifest = output / 'imported-results.json'
    atomic_json(imported_manifest, results)
    atomic_json(output / 'manifest.json', results)
    atomic_json(output / 'import-state.json', {
        'source_manifest_sha256': expected_manifest_sha,
        'source_ledger_sha256': expected_ledger_sha,
        'import_ledger_sha256': sha256(audit),
        'imported_results_sha256': sha256(imported_manifest),
        'validation_tool': results['validation_tool']})
    return {'accepted': accepted, 'fingerprints': fingerprints, 'results': results}


def continuation_identity(manifest, manifest_path, output, checker, coordinator_sha256):
    pin = manifest['validation_tool']
    checker_sha256 = sha256(checker)
    if checker_sha256 != pin['checker_sha256']:
        raise ValueError('validation checker checksum differs from manifest pin')
    if coordinator_sha256 != pin['coordinator_sha256']:
        raise ValueError('validation coordinator checksum differs from manifest pin')
    if not pin.get('revision') or pin['revision'].startswith('PENDING_'):
        raise ValueError('validation coordinator revision is not locked')
    if pin.get('measurement_source_revision') != manifest.get('source_revision'):
        raise ValueError('validation-tool measurement source revision mismatch')
    retry = manifest.get('retry_policy', {})
    if (retry.get('scope') != 'planned_invocation' or retry.get('max_new_attempts') != 3
            or retry.get('legacy_attempts_preserved') is not True):
        raise ValueError('v1.2 retry policy does not match the authorized three-new-attempt contract')
    if manifest.get('status') != 'locked' or manifest.get('execution_authorized') is not True:
        raise ValueError('v1.2 manifest is not locked for execution')
    source = manifest['continuation']
    source_manifest = (manifest_path.parent / source['source_manifest_path']).resolve()
    source_ledger = Path(source['source_ledger_path']).resolve()
    if sha256(source_manifest) != source['source_manifest_sha256']:
        raise ValueError('legacy source manifest checksum mismatch')
    if sha256(source_ledger) != source['source_ledger_sha256']:
        raise ValueError('legacy source ledger checksum mismatch')
    output = Path(output).resolve()
    return {'manifest_sha256': sha256(manifest_path),
            'source_revision': manifest['source_revision'],
            'source_manifest_sha256': source['source_manifest_sha256'],
            'source_ledger_sha256': source['source_ledger_sha256'],
            'checker_sha256': checker_sha256,
            'coordinator_sha256': coordinator_sha256,
            'output': str(output)}


def continuation_results(manifest, accepted, evidence, identity, execution_ledger):
    missing = [entry['planned_run_id'] for entry in manifest['runs']
               if entry['planned_run_id'] not in accepted]
    return {'schema_version': 1, 'protocol_id': manifest.get('protocol_id'),
            'manifest_sha256': identity['manifest_sha256'],
            'source_revision': manifest['source_revision'],
            'source_manifest_sha256': identity['source_manifest_sha256'],
            'source_ledger_sha256': identity['source_ledger_sha256'],
            'validation_tool': {'revision': manifest['validation_tool']['revision'],
                                'checker_sha256': identity['checker_sha256'],
                                'coordinator_sha256': identity['coordinator_sha256']},
            'import_ledger_sha256': sha256(Path(identity['output']) / 'import-attempts.jsonl'),
            'imported_results_sha256': sha256(Path(identity['output']) / 'imported-results.json'),
            'execution_ledger_sha256': sha256(execution_ledger) if execution_ledger.exists() else None,
            'cells': [{'id': cell['id'], 'expected_repetitions': cell['expected_repetitions']}
                      for cell in manifest['cells']],
            'runs': [{'planned_run_id': entry['planned_run_id'], 'group': entry['group'],
                      'cell': entry['cell'], 'repetition': entry['repetition'],
                      'path': accepted[entry['planned_run_id']],
                      'raw_checksums': evidence[entry['planned_run_id']]['raw_checksums'],
                      'config_fingerprint': evidence[entry['planned_run_id']]['config_fingerprint'],
                      'image_fingerprint': evidence[entry['planned_run_id']]['image_fingerprint']}
                     for entry in manifest['runs'] if entry['planned_run_id'] in accepted],
            'missing_planned_run_ids': missing}


def run_imported(args, manifest):
    manifest_path, output = args.manifest.resolve(), args.output.resolve()
    measurement_root = Path(args.measurement_root).resolve()
    checker = Path(args.checker).resolve()
    coordinator_sha256 = args.validation_tool_sha256 or sha256(Path(__file__))
    identity = continuation_identity(manifest, manifest_path, output, checker, coordinator_sha256)
    try:
        output.relative_to(measurement_root)
        raise ValueError('coordinator output must be outside the measurement checkout')
    except ValueError as exc:
        if str(exc).startswith('coordinator output'):
            raise
    import_state_path = output / 'import-state.json'
    import_results_path = output / 'imported-results.json'
    import_ledger = output / 'import-attempts.jsonl'
    execution_ledger = output / 'attempts.jsonl'
    if not all(path.is_file() for path in (import_state_path, import_results_path, import_ledger)):
        raise ValueError('Stage A import outputs are missing; run --import-legacy first')
    import_state = json.loads(import_state_path.read_text())
    if (import_state.get('import_ledger_sha256') != sha256(import_ledger)
            or import_state.get('imported_results_sha256') != sha256(import_results_path)
            or import_state.get('source_manifest_sha256') != identity['source_manifest_sha256']
            or import_state.get('source_ledger_sha256') != identity['source_ledger_sha256']
            or import_state.get('validation_tool', {}).get('checker_sha256') != identity['checker_sha256']
            or import_state.get('validation_tool', {}).get('coordinator_sha256') != identity['coordinator_sha256']):
        raise ValueError('immutable Stage A import evidence or validation tool pin changed')
    imported = json.loads(import_results_path.read_text())
    if (imported.get('manifest_sha256') != identity['manifest_sha256']
            or imported.get('source_revision') != identity['source_revision']
            or imported.get('source_manifest_sha256') != identity['source_manifest_sha256']
            or imported.get('source_ledger_sha256') != identity['source_ledger_sha256']):
        raise ValueError('Stage A results do not match the locked v1.2 manifest/source')

    runs = {entry['planned_run_id']: entry for entry in manifest['runs']}
    accepted, evidence = {}, {}
    for row in imported['runs']:
        run_id = row['planned_run_id']
        if run_id not in runs or run_id in accepted:
            raise ValueError('Stage A results contain an unknown or duplicate planned run')
        details = imported.get('accepted_evidence', {}).get(run_id)
        path = Path(row['path']).resolve()
        if not details or tree_checksums(path) != details.get('raw_checksums'):
            raise ValueError(f'Stage A accepted raw evidence changed: {run_id}')
        if not details.get('config_fingerprint') or not details.get('image_fingerprint'):
            raise ValueError(f'Stage A accepted checker fingerprints missing: {run_id}')
        accepted[run_id] = str(path)
        evidence[run_id] = details
    for entry in manifest['runs']:
        if entry['planned_run_id'] not in accepted and entry['planned_run_id'] not in imported.get('missing_planned_run_ids', []):
            raise ValueError('Stage A result omitted a planned slot without marking it missing')

    history = [json.loads(line) for line in execution_ledger.read_text().splitlines() if line] if execution_ledger.exists() else []
    starts, started_keys, finished, started_paths = Counter(), set(), set(), set()
    seed = [row for row in history if row.get('event') == 'continuation_started']
    if len(seed) > 1 or (seed and seed[0].get('identity') != identity):
        raise ValueError('v1.2 execution ledger identity or imported evidence pin mismatch')
    for row in history:
        if row.get('event') == 'continuation_started':
            continue
        if row.get('event') in ('preflight_passed', 'preflight_failed'):
            if row.get('identity') != identity:
                raise ValueError('v1.2 preflight record identity mismatch')
            continue
        if row.get('event') not in ('attempt_started', 'attempt_finished'):
            raise ValueError('unknown v1.2 execution ledger event')
        ids = row.get('planned_run_ids', [])
        if not ids or row.get('manifest_sha256') != identity['manifest_sha256']:
            raise ValueError('v1.2 attempt lacks planned IDs or has manifest drift')
        if row.get('source_revision') != identity['source_revision']:
            raise ValueError('v1.2 attempt source revision drift')
        if row.get('config') != [runs[run_id]['config'] for run_id in ids] or any(run_id not in runs for run_id in ids):
            raise ValueError('v1.2 attempt config or planned ID drift')
        group = [runs[run_id] for run_id in ids]
        if any(entry['invocation_id'] != row.get('invocation_id') for entry in group):
            raise ValueError('v1.2 attempt invocation mapping drift')
        if row.get('environment') != group[0]['environment'] or any(entry['environment'] != group[0]['environment'] for entry in group):
            raise ValueError('v1.2 attempt environment drift')
        if row.get('event') == 'attempt_started':
            key = (row['invocation_id'], row['attempt'])
            path = str(Path(row['run_path']).resolve())
            if key in finished or path in started_paths or row['attempt'] != starts[row['invocation_id']] + 1:
                raise ValueError('v1.2 attempt number or output path was reused')
            if row['attempt'] > manifest['retry_policy']['max_new_attempts']:
                raise ValueError('v1.2 per-invocation retry limit exceeded')
            starts[row['invocation_id']] += 1
            started_paths.add(path)
            started_keys.add(key)
        else:
            key = (row['invocation_id'], row['attempt'])
            if key not in started_keys or key in finished:
                raise ValueError('v1.2 finished attempt lacks a unique start')
            finished.add(key)
            if row.get('accepted'):
                if set(row.get('accepted_result_paths', {})) != set(ids):
                    raise ValueError('accepted v1.2 invocation does not contain the whole planned group')
                for run_id, path in row['accepted_result_paths'].items():
                    if run_id in accepted:
                        raise ValueError(f'planned run accepted twice: {run_id}')
                    checksums = row.get('evidence_checksums', {}).get(run_id)
                    report = row.get('checks', {}).get(run_id, {})
                    if not checksums or tree_checksums(Path(path)) != checksums or not report.get('valid'):
                        raise ValueError(f'v1.2 accepted raw evidence changed: {run_id}')
                    if not report.get('config_fingerprint') or not report.get('image_fingerprint'):
                        raise ValueError(f'v1.2 accepted checker fingerprints missing: {run_id}')
                    accepted[run_id] = str(Path(path).resolve())
                    evidence[run_id] = {'raw_checksums': checksums,
                                        'config_fingerprint': report.get('config_fingerprint'),
                                        'image_fingerprint': report.get('image_fingerprint')}
    if not seed:
        with execution_ledger.open('a') as stream:
            stream.write(json.dumps({'event': 'continuation_started', 'identity': identity,
                                     'import_state_sha256': sha256(import_state_path),
                                     'started_at_utc': now()}, sort_keys=True) + '\n')
            stream.flush(); os.fsync(stream.fileno())
    elif seed[0].get('import_state_sha256') != sha256(import_state_path):
        raise ValueError('Stage A import state checksum differs from v1.2 execution ledger')

    def append(record):
        with execution_ledger.open('a') as stream:
            stream.write(json.dumps(record, sort_keys=True) + '\n')
            stream.flush(); os.fsync(stream.fileno())

    invocation_groups = groups(manifest['runs'])
    pending = [group for group in invocation_groups
               if (not all(entry['planned_run_id'] in accepted for entry in group)
                   and starts[group[0]['invocation_id']] < manifest['retry_policy']['max_new_attempts'])]
    prior_stops = [row.get('stop_reason') for row in history
                   if row.get('event') == 'attempt_finished' and row.get('stop_reason')]
    prior_stops.extend('preflight_failed:' + row.get('error', 'unknown') for row in history
                       if row.get('event') == 'preflight_failed')
    stopped, stop_reason = bool(prior_stops), (prior_stops[-1] if prior_stops else '')
    observer_dir = None
    before_containers = set()
    if pending and not stopped:
        observer_dir = output / f'clock-observer-v12-{os.getpid()}-{time.time_ns()}'
        try:
            observer = preflight(manifest, manifest_path, observer_dir, measurement_root)
            before_containers = observer['containers']
            append({'event': 'preflight_passed', 'identity': identity, 'observer_path': str(observer_dir),
                    'observer_summary': observer['summary'],
                    'observer_summary_sha256': (sha256(observer_dir / 'summary.json')
                                                if (observer_dir / 'summary.json').exists() else None),
                    'observed_at_utc': now()})
        except (OSError, KeyError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
            stopped, stop_reason = True, 'preflight_failed:' + str(exc)
            append({'event': 'preflight_failed', 'identity': identity, 'observer_path': str(observer_dir),
                    'error': str(exc), 'observed_at_utc': now()})

    for group in pending:
        if stopped:
            break
        ids = [entry['planned_run_id'] for entry in group]
        if any(run_id in accepted for run_id in ids):
            raise ValueError('partially accepted planned invocation in continuation state')
        invocation = group[0]['invocation_id']
        attempt = starts[invocation] + 1
        if attempt > manifest['retry_policy']['max_new_attempts']:
            continue
        while attempt <= manifest['retry_policy']['max_new_attempts']:
            run_output = Path(group[0]['output_path'])
            run_output = run_output if run_output.is_absolute() else measurement_root / run_output
            if attempt > 1:
                run_output = run_output.with_name(run_output.name + f'.attempt-{attempt}')
            run_output = run_output.resolve()
            if str(run_output) in started_paths or run_output.exists():
                raise ValueError(f'v1.2 attempt output path already exists: {run_output}')
            command = [str(run_output) if token in ('<OUTPUT_PATH>', group[0]['output_path']) else
                       str(manifest_path) if token == '<ABSOLUTE_PROTOCOL_V1_2_MANIFEST>' else token
                       for token in group[0]['command']]
            for index, token in enumerate(command[:-1]):
                if token == '--output':
                    command[index + 1] = str(run_output)
            env = os.environ.copy(); env.update(group[0]['environment'])
            start, suspend_before = now(), suspend_gap_ms()
            append({'event': 'attempt_started', 'invocation_id': invocation, 'planned_run_ids': ids,
                    'attempt': attempt, 'run_path': str(run_output), 'source_revision': manifest['source_revision'],
                    'config': [entry['config'] for entry in group], 'environment': group[0]['environment'],
                    'command': command, 'manifest_sha256': identity['manifest_sha256'],
                    'observer_path': str(observer_dir), 'started_at_utc': start,
                    'boottime_minus_monotonic_before_ms': suspend_before})
            starts[invocation] += 1; started_paths.add(str(run_output))
            error, cleanup_error, runner_rc = '', '', 127
            try:
                runner_rc = subprocess.run(command, cwd=measurement_root, env=env, check=False).returncode
            except OSError as exc:
                error = str(exc)
            try:
                check_cleanup(before_containers, measurement_root)
            except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                cleanup_error = str(exc)
            fixed_result, decisions = {'commands': [], 'thresholds': {}}, {}
            if runner_rc == 0 and len(group) == 2 and any(entry.get('fixed_analysis_commands') for entry in group):
                try:
                    fixed_result = fixed_outage_analysis(manifest_path, group, run_output, measurement_root)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    error = 'fixed-threshold analysis failed: ' + str(exc)
            healthy_failed = False
            for entry in group:
                planned_dir = base_path(manifest_path, entry, measurement_root)
                planned_output = Path(group[0]['output_path'])
                planned_output = planned_output if planned_output.is_absolute() else measurement_root / planned_output
                try:
                    suffix = planned_dir.relative_to(planned_output.resolve())
                except ValueError:
                    suffix = Path()
                actual_dir = run_output / suffix
                actual_dir.mkdir(parents=True, exist_ok=True)
                if healthy_failed and entry['cell'].endswith('-outage') and not (actual_dir / 'load/metadata.json').exists():
                    decisions[entry['planned_run_id']] = {'path': str(actual_dir), 'exit_code': runner_rc,
                                                           'stop_sequence': False, 'valid': False,
                                                           'reasons': ['healthy_gate_failed_before_outage']}
                    continue
                quality = actual_dir / 'coordinator-quality-check.json'
                try:
                    decision = checker_call(manifest_path, entry, actual_dir, checker, measurement_root)
                    if not quality.exists():
                        raise ValueError('checker produced no report')
                except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
                    decision = {'exit_code': 2, 'stop_sequence': True, 'valid': False,
                                'reasons': ['checker_setup_or_output_invalid:' + str(exc)]}
                drift = [reason for reason in decision.get('reasons', [])
                         if any(reason.startswith(prefix) for prefix in FATAL_DRIFT_REASONS)]
                cell = entry['cell']
                fingerprint = (decision.get('config_fingerprint'), decision.get('image_fingerprint'))
                if decision.get('valid'):
                    previous = next((evidence[run_id] for run_id in accepted
                                     if runs[run_id]['cell'] == cell), None)
                    if previous and fingerprint != (previous['config_fingerprint'], previous['image_fingerprint']):
                        drift.append('same_cell_fingerprint_drift')
                if drift:
                    decision['valid'] = False
                    decision.setdefault('reasons', []).extend(reason for reason in drift if reason not in decision['reasons'])
                decisions[entry['planned_run_id']] = {'path': str(actual_dir), **decision}
                if entry['cell'].endswith('-healthy') and not decision.get('valid'):
                    healthy_failed = True
                if drift:
                    stopped, stop_reason = True, 'actual_config_image_or_source_drift'
                elif decision.get('stop_sequence') and not any(reason.startswith(('fatal_setup:', 'fatal_artifact:'))
                                                               for reason in decision.get('reasons', [])):
                    stopped, stop_reason = True, 'quality_stop_sequence'
            suspend_after = suspend_gap_ms()
            suspend_delta = (suspend_after - suspend_before if suspend_before is not None and suspend_after is not None else None)
            if suspend_delta is not None and abs(suspend_delta) > manifest.get('clock_tolerance_ms', 5):
                error = f'guest_suspend_detected:{suspend_delta:.6f}ms'
                stopped, stop_reason = True, error
            valid = (runner_rc == 0 and not error and not cleanup_error and len(decisions) == len(group)
                     and all(row.get('exit_code') == 0 and row.get('valid') for row in decisions.values()))
            if cleanup_error:
                stopped, stop_reason = True, 'runner_cleanup_failed:' + cleanup_error
            paths = {run_id: decisions[run_id]['path'] for run_id in ids} if valid else {}
            checksums = {}
            if valid:
                for entry in group:
                    run_id = entry['planned_run_id']; path = Path(paths[run_id])
                    report = decisions[run_id]
                    checksums[run_id] = tree_checksums(path)
                    accepted[run_id] = paths[run_id]
                    evidence[run_id] = {'raw_checksums': checksums[run_id],
                                        'config_fingerprint': report.get('config_fingerprint'),
                                        'image_fingerprint': report.get('image_fingerprint')}
            finished_record = {'event': 'attempt_finished', 'invocation_id': invocation,
                               'planned_run_ids': ids, 'attempt': attempt, 'run_path': str(run_output),
                               'source_revision': manifest['source_revision'],
                               'config': [entry['config'] for entry in group],
                               'environment': group[0]['environment'], 'command': command,
                               'manifest_sha256': identity['manifest_sha256'],
                               'observer_path': str(observer_dir), 'started_at_utc': start,
                               'ended_at_utc': now(), 'runner_exit_code': runner_rc,
                               'setup_error': error, 'cleanup_error': cleanup_error,
                               'fixed_analysis': fixed_result, 'checks': decisions, 'accepted': valid,
                               'accepted_result_paths': paths, 'boottime_minus_monotonic_before_ms': suspend_before,
                               'boottime_minus_monotonic_after_ms': suspend_after,
                               'boottime_minus_monotonic_delta_ms': suspend_delta,
                               'stop_reason': stop_reason if stopped else ''}
            if valid:
                finished_record['evidence_checksums'] = checksums
            append(finished_record); finished.add((invocation, attempt))
            if valid or stopped:
                break
            attempt += 1
        if stopped:
            break
    results = continuation_results(manifest, accepted, evidence, identity, execution_ledger)
    results['observer_path'] = str(observer_dir) if observer_dir else None
    results['observer_summary_sha256'] = (sha256(observer_dir / 'summary.json')
                                          if observer_dir and (observer_dir / 'summary.json').exists() else None)
    results['stop_reason'] = stop_reason
    atomic_json(output / 'manifest.json', results)
    print(f"Accepted {len(accepted)}/{len(manifest['runs'])} planned runs")
    return 2 if stopped else (0 if not results['missing_planned_run_ids'] else 1)


def run(args):
    manifest_path, output = args.manifest.resolve(), args.output.resolve()
    measurement_root = Path(getattr(args, 'measurement_root', ROOT)).resolve()
    checker = Path(getattr(args, 'checker', CHECKER)).resolve()
    ledger = output / 'attempts.jsonl'
    result_path = output / 'manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
        if getattr(args, 'resume_imported', False):
            return run_imported(args, manifest)
        if getattr(args, 'import_legacy', False):
            imported = import_legacy(manifest, manifest_path, output, measurement_root, checker,
                                      getattr(args, 'validation_tool_sha256', None))
            print(f"Imported {len(imported['accepted'])}/{len(manifest['runs'])} planned runs")
            return 0
        if any(entry['source_revision'] != manifest['source_revision'] for entry in manifest['runs']):
            raise ValueError('planned run source revision differs from manifest pin')
        invocation_groups = groups(manifest['runs'])
        try:
            output.relative_to(measurement_root)
            raise ValueError('coordinator output must be outside the measurement checkout')
        except ValueError as exc:
            if str(exc).startswith('coordinator output'):
                raise
        if not args.resume and (ledger.exists() or result_path.exists()):
            raise ValueError('output already exists; use --resume')
        if not args.resume and output.exists() and any(output.iterdir()):
            raise ValueError('output directory is not empty; use a fresh path')
        observer_dir = output / f'clock-observer-{os.getpid()}-{time.time_ns()}'
        observer = preflight(manifest, manifest_path, observer_dir, measurement_root)
        before_containers = observer['containers']
        manifest_hash = sha256(manifest_path)
        output.mkdir(parents=True, exist_ok=True)
        observer_record = {'path': str(observer_dir), 'summary': observer['summary'],
                           'summary_sha256': sha256(observer_dir / 'summary.json') if (observer_dir / 'summary.json').exists() else None,
                           'manifest_sha256': manifest_hash}
        with (output / 'observers.jsonl').open('a') as stream:
            stream.write(json.dumps(observer_record, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        history = [json.loads(line) for line in ledger.read_text().splitlines() if line] if ledger.exists() else []
        expected = {entry['planned_run_id']: entry for entry in manifest['runs']}
        for row in history:
            if row.get('manifest_sha256') != manifest_hash:
                raise ValueError('resume manifest checksum mismatch')
            ids = row.get('planned_run_ids', [])
            if not ids or row.get('config') != [expected[i]['config'] for i in ids] or any(row.get('source_revision') != expected[i]['source_revision'] for i in ids):
                raise ValueError('resume ledger config or revision mismatch')
            if row.get('accepted'):
                for run_id, actual_path in row.get('accepted_result_paths', {}).items():
                    tree = row.get('evidence_checksums', {}).get(run_id, {})
                    if not tree or tree_checksums(Path(actual_path)) != tree:
                        raise ValueError(f'resume accepted evidence missing or changed: {run_id}')
                    report = row.get('checks', {}).get(run_id, {})
                    if not report.get('valid') or not report.get('config_fingerprint') or not report.get('image_fingerprint'):
                        raise ValueError(f'resume accepted checker evidence incomplete: {run_id}')
        accepted = {run_id: path for row in history if row.get('accepted')
                    for run_id, path in row.get('accepted_result_paths', {}).items()}
        retry_counts = defaultdict(int)
        exhausted = set()
        last_attempt = {}
        cell_fingerprints = {}
        for row in history:
            last_attempt[row['invocation_id']] = max(last_attempt.get(row['invocation_id'], 0), row.get('attempt', 1))
            if row.get('event') == 'attempt_started' and row.get('attempt', 1) > 1:
                retry_counts[row['retry_budget_key']] += 1
            if row.get('event') == 'attempt_finished':
                for run_id, report in row.get('checks', {}).items():
                    if report.get('valid'):
                        cell = expected[run_id]['cell']
                        fingerprint = (report.get('config_fingerprint'), report.get('image_fingerprint'))
                        if cell in cell_fingerprints and cell_fingerprints[cell] != fingerprint:
                            raise ValueError(f'resume same-cell fingerprint mismatch: {cell}')
                        cell_fingerprints[cell] = fingerprint
        for row in history:
            if row.get('event') == 'attempt_finished' and not row.get('accepted') and any(run_id not in accepted for run_id in row.get('planned_run_ids', [])) and retry_counts[row['retry_budget_key']] >= 2:
                exhausted.add(row['retry_budget_key'])
        finished_attempts = {(row['invocation_id'], row['attempt']) for row in history if row.get('event') == 'attempt_finished'}
        for row in history:
            if (row.get('event') == 'attempt_started' and (row['invocation_id'], row['attempt']) not in finished_attempts
                    and retry_counts[row['retry_budget_key']] >= 2
                    and any(run_id not in accepted for run_id in row.get('planned_run_ids', []))):
                exhausted.add(row['retry_budget_key'])

        def append(record):
            with ledger.open('a') as stream:
                stream.write(json.dumps(record, sort_keys=True) + '\n')
                stream.flush()
                os.fsync(stream.fileno())

        stop = False
        for group in invocation_groups:
            ids = [entry['planned_run_id'] for entry in group]
            if all(run_id in accepted for run_id in ids):
                continue
            key = ('outage:' + group[0]['config']['policy']['fail_policy']) if len(group) == 2 else 'cell:' + group[0]['cell']
            if key in exhausted:
                continue
            attempt = last_attempt.get(group[0]['invocation_id'], 0) + 1
            while attempt <= 3:
                if attempt > 1 and retry_counts[key] >= 2:
                    break
                run_output = Path(group[0]['output_path'])
                run_output = run_output if run_output.is_absolute() else measurement_root / run_output
                if attempt > 1:
                    run_output = run_output.with_name(run_output.name + f'.attempt-{attempt}')
                if run_output.exists():
                    raise ValueError(f'attempt output already exists: {run_output}')
                command = list(group[0]['command'])
                command = [str(run_output) if token in ('<OUTPUT_PATH>', group[0]['output_path']) else
                           str(manifest_path) if token == '<ABSOLUTE_PROTOCOL_V1_1_MANIFEST>' else token
                           for token in command]
                for index, token in enumerate(command[:-1]):
                    if token == '--output':
                        command[index + 1] = str(run_output)
                env = os.environ.copy()
                env.update(group[0]['environment'])
                start, error = now(), ''
                suspend_before = suspend_gap_ms()
                if attempt > 1:
                    retry_counts[key] += 1
                append({'event': 'attempt_started', 'invocation_id': group[0]['invocation_id'],
                        'planned_run_ids': ids, 'retry_budget_key': key, 'attempt': attempt,
                        'run_path': str(run_output), 'source_revision': group[0]['source_revision'],
                        'config': [e['config'] for e in group], 'environment': group[0]['environment'],
                        'command': command, 'manifest_sha256': manifest_hash,
                        'observer_path': str(observer_dir), 'started_at_utc': start,
                        'boottime_minus_monotonic_before_ms': suspend_before})
                try:
                    proc = subprocess.run(command, cwd=measurement_root, env=env, check=False)
                    runner_rc = proc.returncode
                except OSError as exc:
                    runner_rc, error = 127, str(exc)
                cleanup_error = ''
                try:
                    check_cleanup(before_containers, measurement_root)
                except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                    cleanup_error = str(exc)
                decisions = {}
                fixed_result = {'commands': [], 'thresholds': {}}
                if runner_rc == 0 and len(group) == 2 and any(e.get('fixed_analysis_commands') for e in group):
                    try:
                        fixed_result = fixed_outage_analysis(manifest_path, group, run_output, measurement_root)
                    except (OSError, ValueError, subprocess.SubprocessError) as exc:
                        error = f'fixed-threshold analysis failed: {exc}'
                if not error and runner_rc != 127:
                    healthy_gate_failed = False
                    for entry in group:
                        planned_dir = base_path(manifest_path, entry, measurement_root)
                        planned_output = Path(group[0]['output_path'])
                        planned_output = planned_output if planned_output.is_absolute() else measurement_root / planned_output
                        try:
                            relative = planned_dir.relative_to(planned_output.resolve())
                        except ValueError:
                            relative = Path()
                        actual_dir = run_output / relative
                        actual_dir.mkdir(parents=True, exist_ok=True)
                        if healthy_gate_failed and entry['cell'].endswith('-outage') and not (actual_dir / 'load/metadata.json').exists():
                            decisions[entry['planned_run_id']] = {'path': str(actual_dir), 'exit_code': runner_rc,
                                'stop_sequence': False, 'valid': False, 'reasons': ['healthy_gate_failed_before_outage']}
                            continue
                        try:
                            decision = checker_call(manifest_path, entry, actual_dir, checker, measurement_root)
                        except (OSError, ValueError, json.JSONDecodeError) as exc:
                            decision = {'exit_code': 2, 'stop_sequence': True, 'valid': False,
                                        'reasons': ['checker_setup_or_output_invalid:' + str(exc)]}
                        cell = entry['cell']
                        fingerprints = (decision.get('config_fingerprint'), decision.get('image_fingerprint'))
                        if decision.get('valid') and cell in cell_fingerprints and fingerprints != cell_fingerprints[cell]:
                            decision['valid'] = False
                            decision.setdefault('reasons', []).append('same_cell_fingerprint_mismatch')
                        decisions[entry['planned_run_id']] = {'path': str(actual_dir), **decision}
                        if runner_rc != 0 and entry['cell'].endswith('-healthy') and not decision.get('valid') and not decision.get('stop_sequence'):
                            healthy_gate_failed = True
                suspend_after = suspend_gap_ms()
                suspend_delta = suspend_after - suspend_before if suspend_before is not None and suspend_after is not None else None
                if suspend_delta is not None and abs(suspend_delta) > manifest.get('clock_tolerance_ms', 5):
                    error = f'guest_suspend_detected:{suspend_delta:.6f}ms'
                end = now()
                valid = runner_rc == 0 and not error and not cleanup_error and len(decisions) == len(group) and all(x.get('exit_code') == 0 and x.get('valid') for x in decisions.values())
                for entry in group:
                    if valid:
                        accepted[entry['planned_run_id']] = decisions[entry['planned_run_id']]['path']
                record = {'event': 'attempt_finished', 'invocation_id': group[0]['invocation_id'], 'planned_run_ids': ids,
                          'retry_budget_key': key, 'attempt': attempt, 'run_path': str(run_output),
                          'source_revision': group[0]['source_revision'], 'config': [e['config'] for e in group],
                          'environment': group[0]['environment'], 'command': command, 'manifest_sha256': manifest_hash,
                          'observer_path': str(observer_dir),
                          'boottime_minus_monotonic_before_ms': suspend_before,
                          'boottime_minus_monotonic_after_ms': suspend_after,
                          'boottime_minus_monotonic_delta_ms': suspend_delta,
                          'started_at_utc': start, 'ended_at_utc': end, 'runner_exit_code': runner_rc,
                          'setup_error': error, 'cleanup_error': cleanup_error, 'fixed_analysis': fixed_result,
                          'checks': decisions, 'accepted': valid,
                          'accepted_result_paths': {i: accepted[i] for i in ids} if valid else {}}
                if valid:
                    record['evidence_checksums'] = {i: tree_checksums(Path(accepted[i])) for i in ids}
                append(record)
                if valid:
                    for entry in group:
                        report = decisions[entry['planned_run_id']]
                        cell_fingerprints.setdefault(entry['cell'], (report.get('config_fingerprint'), report.get('image_fingerprint')))
                if valid:
                    break
                if error or cleanup_error or any(value.get('stop_sequence') for value in decisions.values()):
                    stop = True
                    break
                if retry_counts[key] >= 2:
                    break
                attempt += 1
            if stop:
                break
            if not all(run_id in accepted for run_id in ids) and retry_counts[key] >= 2:
                exhausted.add(key)

        results = {'clock_tolerance_ms': manifest['clock_tolerance_ms'],
                   'cells': [{'id': cell['id'], 'expected_repetitions': cell['expected_repetitions']} for cell in manifest['cells']],
                   'runs': [{'planned_run_id': entry['planned_run_id'], 'group': entry['group'], 'cell': entry['cell'], 'repetition': entry['repetition'], 'path': accepted[entry['planned_run_id']]}
                            for entry in manifest['runs'] if entry['planned_run_id'] in accepted]}
        encoded_results = json.dumps(results, indent=2) + '\n'
        temp_result = result_path.with_name(result_path.name + '.tmp')
        temp_result.write_text(encoded_results)
        os.replace(temp_result, result_path)
        print(f"Accepted {len(accepted)}/{len(manifest['runs'])} planned runs")
        return 2 if stop else (0 if len(accepted) == len(manifest['runs']) else 1)
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f'run-study: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--measurement-root', type=Path, default=ROOT,
                        help='pinned 029 checkout used for execution and source evidence')
    parser.add_argument('--checker', type=Path, default=CHECKER,
                        help='checker version run outside the pinned measurement source')
    parser.add_argument('--import-legacy', action='store_true',
                        help='offline revalidation of the immutable continuation source ledger')
    parser.add_argument('--resume-imported', action='store_true',
                        help='execute only missing v1.2 invocations from the immutable Stage A import')
    parser.add_argument('--validation-tool-sha256',
                        help='explicit SHA-256 of the separately versioned validation coordinator')
    raise SystemExit(run(parser.parse_args()))
