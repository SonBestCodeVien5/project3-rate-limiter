#!/usr/bin/env python3
"""Run the locked manifest sequentially and retain every attempt."""
import argparse
from collections import defaultdict
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
                       'policy_mismatch:', 'workload_config_mismatch:', 'topology_mismatch',
                       'backend_config_mismatch', 'topology_policy_mismatch:',
                       'topology_policy_evidence_mismatch', 'namespace_mismatch:')


def import_legacy(manifest, manifest_path, output, measurement_root=ROOT,
                  checker=CHECKER, validation_tool_sha256=None):
    """Revalidate immutable v1.1 attempts into a fresh v1.2 continuation output."""
    continuation = manifest['continuation']
    checker_sha256 = sha256(checker)
    coordinator_sha256 = validation_tool_sha256 or sha256(Path(__file__))
    tool_pin = manifest.get('validation_tool', {})
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
    accepted, fingerprints = {}, {}
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
               'source_revision': manifest['source_revision'],
               'source_manifest_sha256': expected_manifest_sha, 'source_ledger_sha256': expected_ledger_sha,
               'validation_tool': {'checker_sha256': checker_sha256,
                                   'coordinator_sha256': coordinator_sha256,
                                   'revision': tool_pin.get('revision')},
               'cells': [{'id': cell['id'], 'expected_repetitions': cell['expected_repetitions']}
                         for cell in manifest['cells']],
               'runs': [{'planned_run_id': entry['planned_run_id'], 'group': entry['group'], 'cell': entry['cell'],
                         'repetition': entry['repetition'], 'path': accepted[entry['planned_run_id']]}
                        for entry in manifest['runs'] if entry['planned_run_id'] in accepted],
               'missing_planned_run_ids': [entry['planned_run_id'] for entry in manifest['runs']
                                           if entry['planned_run_id'] not in accepted]}
    (output / 'manifest.json').write_text(json.dumps(results, indent=2) + '\n')
    return {'accepted': accepted, 'fingerprints': fingerprints, 'results': results}


def run(args):
    manifest_path, output = args.manifest.resolve(), args.output.resolve()
    measurement_root = Path(getattr(args, 'measurement_root', ROOT)).resolve()
    checker = Path(getattr(args, 'checker', CHECKER)).resolve()
    ledger = output / 'attempts.jsonl'
    result_path = output / 'manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
        if getattr(args, 'import_legacy', False):
            imported = import_legacy(manifest, manifest_path, output, measurement_root, checker,
                                      getattr(args, 'validation_tool_sha256', None))
            print(f"Imported {len(imported['accepted'])}/{len(manifest['runs'])} planned runs")
            return 0 if len(imported['accepted']) == len(manifest['runs']) else 1
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
    parser.add_argument('--validation-tool-sha256',
                        help='explicit SHA-256 of the separately versioned validation coordinator')
    raise SystemExit(run(parser.parse_args()))
