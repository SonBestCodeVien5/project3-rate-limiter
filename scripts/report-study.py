#!/usr/bin/env python3
"""Export explicitly selected study runs; never pool traces or infer winners."""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import median

SUMMARY_METRICS = ('sent', 'scheduled', 'generator_dropped', 'http_2xx', 'http_429', 'http_5xx', 'transport_errors', 'timeouts', 'sent_per_second', 'completed_per_second', 'legitimate_goodput_per_second')


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def load_json(path, flags):
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict) and not (path.name in ('images.json', 'image-inspect.json') and isinstance(value, list)):
            raise ValueError('expected object/array')
        return value
    except (OSError, ValueError) as error:
        flags.append(f'missing_or_malformed:{path.name}:{type(error).__name__}')
        return {}


def text(path, flags):
    try:
        return path.read_text().strip()
    except OSError:
        flags.append(f'missing:{path.name}')
        return ''


def timestamp(value):
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.utcoffset() is None:
        raise ValueError('timestamp requires timezone')
    return date.timestamp()


def image_identity(image, inspect, flags):
    exact = {'id': image.get('ID'), 'platform': image.get('Platform')}
    if not image.get('ID'):
        flags.append('missing_image_identity')
    if inspect is None:
        return exact
    matches = [item for item in inspect if isinstance(item, dict) and item.get('Id') == image.get('ID')] if isinstance(inspect, list) else []
    item = matches[0] if len(matches) == 1 else {}
    rootfs = item.get('RootFS', {})
    layers = rootfs.get('Layers') if isinstance(rootfs, dict) else None
    valid_layers = isinstance(layers, list) and bool(layers) and all(isinstance(layer, str) and len(layer) == 71 and layer.startswith('sha256:') and all(char in '0123456789abcdef' for char in layer[7:]) for layer in layers)
    if not valid_layers or rootfs.get('Type') != 'layers' or not isinstance(item.get('Config'), dict) or not item.get('Os') or not item.get('Architecture'):
        flags.append('image_inspect_invalid_or_unmatched:' + str(image.get('ID')))
        return exact
    return {'layers': layers, 'config': item['Config'], 'os': item['Os'], 'arch': item['Architecture'], 'variant': item.get('Variant', ''), 'platform': image.get('Platform')}


def read_run(entry, base, clock_tolerance_ms):
    path = (base / entry['path']).resolve()
    invalid, warnings = [], []
    summary = load_json(path / 'load/summary.json', invalid)
    analysis = load_json(path / 'analysis.json', invalid)
    metadata = load_json(path / 'load/metadata.json', invalid)
    policy = load_json(path / 'policy.json', invalid)
    compose = load_json(path / 'compose-resolved.json', invalid)
    images = load_json(path / 'images.json', invalid)
    inspect_path = path / 'image-inspect.json'
    inspect = load_json(inspect_path, invalid) if inspect_path.exists() else None
    config = metadata.get('config', {})
    if not isinstance(config, dict):
        invalid.append('malformed_workload_config')
        config = {}
    if not config.get('run_id') or summary.get('run_id') != config.get('run_id') or analysis.get('run_id') != config.get('run_id'):
        invalid.append('run_id_mismatch_or_missing')
    required_policy = ('mode', 'algorithm', 'fail_policy', 'limit', 'window_ms', 'capacity', 'rate_per_sec', 'state_reset')
    if any(policy.get(key) is None for key in required_policy) or policy.get('state_reset') is not True:
        invalid.append('missing_policy_or_reset')
    if policy.get('mode') not in ('none', 'local', 'redis') or policy.get('algorithm') not in ('fixed-window', 'token-bucket') or policy.get('fail_policy') not in ('open', 'closed') or any(not numeric(policy.get(key)) or policy[key] <= 0 for key in ('limit', 'window_ms', 'capacity', 'rate_per_sec')):
        invalid.append('invalid_policy_values')
    for label, key in (('mode_label', 'mode'), ('algorithm_label', 'algorithm'), ('fail_policy_label', 'fail_policy')):
        if config.get(label) != policy.get(key):
            invalid.append('workload_policy_label_mismatch:' + label)
    if analysis.get('policy') != policy:
        invalid.append('analysis_policy_mismatch')
    revision = text(path.parent / 'git-revision.txt', invalid)
    dirty = text(path.parent / 'git-status.txt', invalid)
    if not revision or revision != metadata.get('git_revision'):
        invalid.append('revision_mismatch_or_missing')
    if dirty or metadata.get('git_status_porcelain') != '':
        warnings.append('dirty_working_tree_unverified_content')
        invalid.append('dirty_working_tree')
    services = compose.get('services', {})
    apis = sorted(key for key in services if key.startswith('api') and key[3:].isdigit())
    if not apis or any(key not in services for key in ('backend', 'redis', 'nginx')):
        invalid.append('missing_topology')
    backend_env = services.get('backend', {}).get('environment', {})
    if not backend_env.get('BACKEND_CAPACITY') or not backend_env.get('BACKEND_SERVICE_TIME'):
        invalid.append('missing_backend_configuration')
    for name in apis:
        env = services[name].get('environment', {})
        if env.get('MODE') != policy.get('mode') or env.get('ALGORITHM') != policy.get('algorithm'):
            invalid.append('compose_policy_mismatch:' + name)
    image_ids = {}
    if isinstance(images, list):
        for image in images:
            name = image.get('ContainerName', '').rsplit('-', 2)
            if len(name) == 3:
                image_ids[name[1]] = image_identity(image, inspect, invalid)
    if any(not image_ids.get(name) for name in [*apis, 'backend', 'redis', 'nginx']):
        invalid.append('missing_image_identity')
    workload = {key: value for key, value in config.items() if key != 'run_id'}
    for key in ('profile', 'duration_ns', 'rps', 'legitimate_rps', 'legitimate_clients', 'max_inflight', 'timeout_ns', 'max_schedule_lag_ns'):
        if key not in workload:
            invalid.append('missing_workload:' + key)
    topology = {name: {key: value for key, value in service.items() if key in ('image', 'command', 'ports', 'environment')} for name, service in services.items()}
    for name in apis:
        topology[name]['environment'] = {key: value for key, value in services[name].get('environment', {}).items() if key != 'NAMESPACE'}
    normalized_policy = {key: value for key, value in policy.items() if key != 'namespace'}
    context = {'policy': normalized_policy, 'workload': workload, 'topology': topology, 'images': image_ids, 'base_images': text(path / 'base-image-digests.txt', invalid), 'nginx': text(path / 'topology/nginx.conf', invalid), 'revision': revision, 'runtime': {key: metadata.get(key) for key in ('workload_version', 'go_version', 'os', 'arch', 'cpu_count', 'gomaxprocs', 'hostname')}}
    if not context['base_images'] or not context['nginx']:
        invalid.append('missing_base_images_or_nginx')
    if any(value is None for value in context['runtime'].values()):
        invalid.append('missing_runtime')
    row = {'group': entry['group'], 'cell': entry['cell'], 'repetition': str(entry['repetition']), 'path': str(path), 'run_id': summary.get('run_id'), 'oracle_status': analysis.get('oracle', {}).get('status', 'missing')}
    row['observed_oracle_violations'] = len(analysis.get('oracle', {}).get('violations', []))
    envelope = analysis.get('oracle', {}).get('observed_global_accepted_envelope', [])
    bounds = [item.get('shared_quota_overshoot_lower_bound', item.get('above_single_shared_bucket_lower_bound')) for item in envelope]
    row['max_global_envelope_overshoot_lower_bound'] = max((value for value in bounds if numeric(value)), default=None)
    for key in SUMMARY_METRICS:
        row[key] = summary.get(key)
        if not numeric(row[key]):
            invalid.append('missing_metric:' + key)
    for key in ('p50_ms', 'p95_ms', 'p99_ms'):
        row['legitimate_' + key] = summary.get('legitimate_success_latency', {}).get(key) if summary.get('legitimate_successful', 0) > 0 else None
    deltas = analysis.get('counter_deltas', {})
    for key in ('arrivals', 'overload'):
        row['backend_' + key] = deltas.get('backend', {}).get(key)
        if not numeric(row['backend_' + key]):
            invalid.append('missing_backend_counter:' + key)
    errors = [deltas.get(name, {}).get('limiter_errors') for name in apis]
    row['limiter_errors'] = sum(errors) if errors and all(numeric(value) for value in errors) else None
    if row['limiter_errors'] is None:
        invalid.append('missing_api_counters')
    for key in ('average_cpu_cores', 'memory_bytes_first', 'memory_bytes_last'):
        row['redis_' + key] = analysis.get('redis_resources', {}).get(key)
    evidence = analysis.get('evidence', {})
    if evidence.get('summary_counts_match_trace') is not True:
        invalid.append('analyzer_trace_counts_unverified')
    if evidence.get('trace_has_unknown_decisions'):
        warnings.append('unknown_decisions_correctness_limited')
    if summary.get('canceled') is not False:
        invalid.append('canceled_or_missing_state')
    if summary.get('generator_dropped', 0):
        invalid.append('generator_drops')
    for key in ('transport_errors', 'timeouts', 'http_5xx', 'limiter_errors'):
        if row.get(key):
            warnings.append(key + '_observed')
    discrepancies, sent, scheduled, ids = [], 0, 0, set()
    try:
        with (path / 'load/requests.jsonl').open() as trace:
            for line in trace:
                request = json.loads(line)
                scheduled += 1
                if not request.get('request_id') or request['request_id'] in ids:
                    invalid.append('trace_request_ids_invalid')
                ids.add(request.get('request_id'))
                if request.get('sent_at'):
                    sent += 1
                    if request.get('limiter_decision') not in ('allow', 'reject', 'fail-open', 'fail-closed', 'disabled'):
                        warnings.append('unknown_decisions_correctness_limited')
                    lag = request.get('schedule_lag_ms')
                    if not numeric(lag):
                        raise ValueError('missing monotonic schedule lag')
                    discrepancies.append(abs((timestamp(request['sent_at']) - timestamp(request['scheduled_at'])) * 1000 - lag))
                    latency = request.get('latency_ms')
                    if not numeric(latency):
                        raise ValueError('missing monotonic request latency')
                    discrepancies.append(abs((timestamp(request['end_at']) - timestamp(request['sent_at'])) * 1000 - latency))
        if sent != summary.get('sent') or scheduled != summary.get('scheduled') or scheduled - sent != summary.get('generator_dropped'):
            invalid.append('trace_counts_mismatch')
    except (OSError, ValueError, KeyError, TypeError):
        invalid.append('missing_or_malformed_trace')
    row['clock_wall_monotonic_max_delta_ms'] = max(discrepancies, default=None)
    if discrepancies and max(discrepancies) > clock_tolerance_ms:
        invalid.append('client_clock_discontinuity_suspected')
    row['fingerprint'] = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    row['tooling_validity'] = 'invalid' if invalid else 'usable'
    row['quality_flags'] = ';'.join(sorted(set(invalid + warnings)))
    outage = analysis.get('outage') or {}
    for phase, data in outage.get('phases', {}).items():
        row['outage_' + phase + '_legitimate_availability'] = data.get('legitimate_availability')
    row['stable_recovery_ms'] = outage.get('recovery', {}).get('stable_recovery_ms')
    row['recovery_status'] = outage.get('recovery', {}).get('status', 'not_applicable')
    return row


def summarize(rows, cells):
    results = []
    for cell in cells:
        selected = [row for row in rows if row['cell'] == cell['id']]
        reasons = []
        if len(selected) != cell['expected_repetitions'] or len({row['repetition'] for row in selected}) != len(selected):
            reasons.append('repetition_count_or_labels')
        if len({row['fingerprint'] for row in selected}) != 1 or len({row['group'] for row in selected}) != 1:
            reasons.append('incompatible_config')
        if any(row['tooling_validity'] != 'usable' for row in selected):
            reasons.append('invalid_run_evidence')
        result = {'cell': cell['id'], 'runs': len(selected), 'expected_repetitions': cell['expected_repetitions'], 'aggregation_status': ';'.join(reasons) if reasons else 'complete_same_config'}
        if not reasons:
            for key in selected[0]:
                values = [row.get(key) for row in selected]
                if key != 'repetition' and all(numeric(value) for value in values):
                    result.update({key + '_run_median': median(values), key + '_run_min': min(values), key + '_run_max': max(values)})
        results.append(result)
    return results


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export(manifest_path, output):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text())
    cells, entries = manifest['cells'], manifest['runs']
    if not cells or not entries or len({cell['id'] for cell in cells}) != len(cells):
        raise ValueError('nonempty unique cells and explicit runs required')
    for cell in cells:
        if type(cell['expected_repetitions']) is not int or cell['expected_repetitions'] < 1:
            raise ValueError('expected_repetitions must be positive integer')
    if any(entry['cell'] not in {cell['id'] for cell in cells} for entry in entries):
        raise ValueError('run references unknown cell')
    paths = [(manifest_path.parent / entry['path']).resolve() for entry in entries]
    if len(set(paths)) != len(paths):
        raise ValueError('same run path cannot be counted twice')
    tolerance = manifest['clock_tolerance_ms']
    if not numeric(tolerance) or tolerance < 0:
        raise ValueError('clock_tolerance_ms must be explicit nonnegative number')
    rows = []
    for entry in entries:
        try:
            rows.append(read_run(entry, manifest_path.parent, tolerance))
        except (ValueError, TypeError, AttributeError, KeyError) as error:
            rows.append({'group': entry['group'], 'cell': entry['cell'], 'repetition': str(entry['repetition']), 'path': str((manifest_path.parent / entry['path']).resolve()), 'run_id': None, 'oracle_status': 'missing', 'fingerprint': 'malformed', 'tooling_validity': 'invalid', 'quality_flags': 'malformed_evidence:' + type(error).__name__})
    aggregates = summarize(rows, cells)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'runs.csv', rows)
    write_csv(output / 'cells.csv', aggregates)
    lines = ['# Study artifact report', '', 'Measured artifacts only. No winner or final research conclusion is inferred.', '', 'Business problem → pain point → business impact → technical requirement → solution → experiment → evaluation → future development must be supplied in the research report.', '', 'Tooling validity, correctness oracle and research claims are separate. FW inconclusive/partial windows do not invalidate a run by themselves. Errors/overload may be intended outcomes; flags require interpretation against the locked protocol.', '', 'Cell statistics are median/min/max of separate run metrics. A median of run p95/p99 is not a pooled percentile. No aggregation is exported for incomplete, incompatible or invalid-evidence cells.', '', 'Client clock check compares wall-clock sent−scheduled with monotonic schedule lag; it cannot diagnose server clock steps. Tolerance (ms): ' + str(tolerance), '', '| Cell | Runs / expected | Aggregation |', '| --- | --- | --- |']
    lines += [f"| {row['cell']} | {row['runs']} / {row['expected_repetitions']} | {row['aggregation_status']} |" for row in aggregates]
    lines += ['', '| Cell | Metric | Median of runs | Run min | Run max |', '| --- | --- | --- | --- | --- |']
    for cell in aggregates:
        for key in ('legitimate_goodput_per_second', 'legitimate_p95_ms', 'legitimate_p99_ms', 'http_429', 'http_5xx', 'backend_arrivals', 'backend_overload'):
            if key + '_run_median' in cell:
                lines.append(f"| {cell['cell']} | {key} | {cell[key + '_run_median']} | {cell[key + '_run_min']} | {cell[key + '_run_max']} |")
    lines += ['', '| Run / repetition | Tooling | Oracle | Flags |', '| --- | --- | --- | --- |']
    lines += [f"| {row['run_id']} / {row['repetition']} | {row['tooling_validity']} | {row['oracle_status']} | {row['quality_flags'] or 'none'} |" for row in rows]
    lines += ['', 'This exporter writes CSV/Markdown only. Use the separate offline plot-calibration.py for selected pilot charts; no runtime dependency was added.', '']
    (output / 'report.md').write_text('\n'.join(lines))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return rows, aggregates


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--output', required=True, help='new output directory; existing paths are refused')
    args = parser.parse_args()
    export(args.manifest, args.output)
