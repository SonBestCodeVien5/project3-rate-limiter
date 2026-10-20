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


def base_path(manifest_path, entry):
    output = Path(entry['output_path'])
    result = Path(entry['result_path'])
    if output.is_absolute():
        try:
            return result.resolve() if result.is_absolute() else (ROOT / output / result).resolve()
        except OSError:
            pass
    marker = str(output).rstrip('/')
    raw = str(result)
    if marker not in raw:
        raise ValueError(f"result_path does not identify output_path for {entry['planned_run_id']}")
    suffix = raw.split(marker, 1)[1].lstrip('/')
    return (ROOT / output / suffix).resolve()


def sha256(path):
    import hashlib
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def tree_checksums(path):
    return {str(item.relative_to(path)): sha256(item) for item in sorted(path.rglob('*')) if item.is_file()}


def docker_snapshot():
    output = subprocess.check_output(['docker', 'ps', '-aq'], cwd=ROOT, text=True)
    ids = output.split()
    if not ids:
        return set()
    details = json.loads(subprocess.check_output(['docker', 'inspect', *ids], cwd=ROOT, text=True))
    return {item['Id'] for item in details if item.get('Config', {}).get('Labels', {}).get('com.docker.compose.project', '').startswith(('project3-research-lab', 'project3-outage-'))}


def preflight(manifest, manifest_path, observer_dir):
    if manifest.get('execution_authorized') is not True or manifest.get('status') != 'locked':
        raise ValueError('manifest is a draft or execution is not authorized')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if revision != manifest['source_revision'] or dirty.strip():
        raise ValueError('measurement checkout must be clean at the manifest source_revision')
    for key in ('redis_image', 'nginx_image'):
        expected = manifest['runtime'][key]
        inspect = json.loads(subprocess.check_output(['docker', 'image', 'inspect', expected['configured_reference']], cwd=ROOT, text=True))[0]
        if inspect.get('Id') != expected['inspected_id'] or expected['repo_digest'] not in inspect.get('RepoDigests', []):
            raise ValueError(f'pinned local base image mismatch: {key}')
    before = docker_snapshot()
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/observe-clock.py'), '--output', str(observer_dir), '--duration-seconds', '90'], cwd=ROOT, check=False)
    if result.returncode:
        raise ValueError('fresh 90-second clock observer failed')
    summary = json.loads((observer_dir / 'summary.json').read_text())
    if summary.get('duration_seconds') != 90 or summary.get('elapsed_monotonic_seconds', 0) < 89.9 or summary.get('clock_steps_above_5ms'):
        raise ValueError('fresh 90-second observer did not pass the clock gate')
    return {'containers': before, 'summary': summary}


def check_cleanup(before):
    leaked = docker_snapshot() - before
    if leaked:
        raise RuntimeError('runner left Compose containers behind: ' + ','.join(sorted(leaked)))


def checker_call(manifest_path, entry, run_dir):
    quality = run_dir / 'coordinator-quality-check.json'
    check = subprocess.run([sys.executable, str(CHECKER), '--manifest', str(manifest_path), '--planned-run-id', entry['planned_run_id'], '--run-dir', str(run_dir), '--output', str(quality)], cwd=ROOT, check=False)
    decision = {'exit_code': check.returncode, 'stop_sequence': check.returncode == 2}
    if quality.exists():
        decision.update(json.loads(quality.read_text()))
    return decision


def fixed_outage_analysis(manifest_path, group, run_output):
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
                    source = ROOT / source
                destination = Path(actual[3])
                if not destination.is_absolute():
                    destination = ROOT / destination
                destination.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(['cp', '-p', str(source), str(destination)], cwd=ROOT, check=True)
                completed.append(actual)
            else:
                subprocess.run(actual, cwd=ROOT, check=True)
                completed.append(actual)
                if '--recovery-p95-ms' in actual:
                    threshold = actual[actual.index('--recovery-p95-ms') + 1]
                    phase = Path(actual[actual.index('scripts/analyze.py') + 1])
                    phase = phase if phase.is_absolute() else ROOT / phase
                    (phase / 'fixed-recovery-p95-threshold-ms.txt').write_text(threshold + '\n')
                    thresholds[str(phase)] = threshold
    return {'commands': completed, 'thresholds': thresholds}


def run(args):
    manifest_path, output = args.manifest.resolve(), args.output.resolve()
    ledger = output / 'attempts.jsonl'
    result_path = output / 'manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
        if any(entry['source_revision'] != manifest['source_revision'] for entry in manifest['runs']):
            raise ValueError('planned run source revision differs from manifest pin')
        invocation_groups = groups(manifest['runs'])
        try:
            output.relative_to(ROOT)
            raise ValueError('coordinator output must be outside the measurement checkout')
        except ValueError as exc:
            if str(exc).startswith('coordinator output'):
                raise
        if not args.resume and (ledger.exists() or result_path.exists()):
            raise ValueError('output already exists; use --resume')
        if not args.resume and output.exists() and any(output.iterdir()):
            raise ValueError('output directory is not empty; use a fresh path')
        observer_dir = output / f'clock-observer-{os.getpid()}-{time.time_ns()}'
        observer = preflight(manifest, manifest_path, observer_dir)
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
                run_output = run_output if run_output.is_absolute() else ROOT / run_output
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
                    proc = subprocess.run(command, cwd=ROOT, env=env, check=False)
                    runner_rc = proc.returncode
                except OSError as exc:
                    runner_rc, error = 127, str(exc)
                cleanup_error = ''
                try:
                    check_cleanup(before_containers)
                except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                    cleanup_error = str(exc)
                decisions = {}
                fixed_result = {'commands': [], 'thresholds': {}}
                if runner_rc == 0 and len(group) == 2 and any(e.get('fixed_analysis_commands') for e in group):
                    try:
                        fixed_result = fixed_outage_analysis(manifest_path, group, run_output)
                    except (OSError, ValueError, subprocess.SubprocessError) as exc:
                        error = f'fixed-threshold analysis failed: {exc}'
                if not error and runner_rc != 127:
                    healthy_gate_failed = False
                    for entry in group:
                        planned_dir = base_path(manifest_path, entry)
                        planned_output = Path(group[0]['output_path'])
                        planned_output = planned_output if planned_output.is_absolute() else ROOT / planned_output
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
                            decision = checker_call(manifest_path, entry, actual_dir)
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
    raise SystemExit(run(parser.parse_args()))
