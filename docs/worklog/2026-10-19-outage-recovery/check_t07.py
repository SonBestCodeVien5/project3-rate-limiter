#!/usr/bin/env python3
"""Check the bounded T07 healthy/outage artifacts without rejecting expected fallback."""
import datetime as dt
import json
import math
from pathlib import Path
import sys


def epoch(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def check(root):
    root = Path(root)
    results = []
    run_ids = set()
    for policy in ('open', 'closed'):
        healthy = root / policy / 'healthy'
        outage = root / policy / 'outage'
        hp = json.loads((healthy / 'policy.json').read_text())
        op = json.loads((outage / 'policy.json').read_text())
        for key, expected in (('mode', 'redis'), ('algorithm', 'fixed-window'), ('fail_policy', policy),
                              ('limit', 20), ('window_ms', 1000), ('capacity', 20), ('rate_per_sec', 20)):
            assert hp.get(key) == expected and op.get(key) == expected, f'{policy}: policy {key}'
        assert hp['namespace'] != op['namespace'], f'{policy}: namespace collision'
        healthy_compose = json.loads((healthy / 'compose-resolved.json').read_text())
        outage_compose = json.loads((outage / 'compose-resolved.json').read_text())
        assert sorted(healthy_compose['services']) == ['api1', 'api2', 'backend', 'nginx', 'redis']
        assert sorted(outage_compose['services']) == ['api1', 'api2', 'backend', 'nginx', 'redis']
        assert healthy_compose['services']['backend']['environment']['BACKEND_CAPACITY'] == '10'
        assert outage_compose['services']['backend']['environment']['BACKEND_CAPACITY'] == '10'
        assert healthy_compose['services']['backend']['environment']['BACKEND_SERVICE_TIME'] == '50ms'
        assert outage_compose['services']['backend']['environment']['BACKEND_SERVICE_TIME'] == '50ms'
        for config in (healthy_compose, outage_compose):
            for api in ('api1', 'api2'):
                env = config['services'][api]['environment']
                assert env['MODE'] == 'redis' and env['ALGORITHM'] == 'fixed-window' and env['FAIL_POLICY'] == policy
                assert env['LIMIT'] == '20' and env['WINDOW'] == '1s' and env['CAPACITY'] == '20' and env['RATE'] == '20'
        def matched(value):
            value = json.loads(json.dumps(value))
            services = value['services']
            for service in services.values():
                service.get('environment', {}).pop('NAMESPACE', None)
                for mount in service.get('volumes', []):
                    if 'source' in mount:
                        mount['source'] = Path(mount['source']).name
            return services
        assert matched(healthy_compose) == matched(outage_compose), f'{policy}: healthy/outage topology mismatch'
        assert (healthy.parent / 'git-revision.txt').read_text().strip() == '09b1249a08adf441062f8f6918b771b5cb8852e8'
        assert (healthy.parent / 'git-status.txt').read_text() == ''
        assert (outage.parent / 'git-revision.txt').read_text().strip() == '09b1249a08adf441062f8f6918b771b5cb8852e8'
        assert (outage.parent / 'git-status.txt').read_text() == ''
        phase_results = {}
        for phase, case in (('healthy', healthy), ('outage', outage)):
            metadata = json.loads((case / 'load/metadata.json').read_text())
            summary = json.loads((case / 'load/summary.json').read_text())
            analysis = json.loads((case / 'analysis.json').read_text())
            compose = json.loads((case / 'compose-resolved.json').read_text())
            rows = [json.loads(line) for line in (case / 'load/requests.jsonl').read_text().splitlines() if line]
            config = metadata['config']
            assert metadata['git_revision'] == '09b1249a08adf441062f8f6918b771b5cb8852e8'
            assert metadata['git_status_porcelain'] == ''
            assert config['duration_ns'] == 30_000_000_000 and config['rps'] == 100 and config['legitimate_rps'] == 20
            assert config['run_id'].startswith(f't07-') and config['run_id'].endswith(f'-{policy}-{phase}')
            assert config['run_id'] not in run_ids, f'duplicate run ID: {config["run_id"]}'
            run_ids.add(config['run_id'])
            assert summary['run_id'] == config['run_id'] and analysis['run_id'] == config['run_id']
            assert summary['scheduled'] == summary['sent'] == len(rows) == 3000
            assert summary['generator_dropped'] == 0 and summary['canceled'] is False
            assert sum(bool(r.get('sent_at')) for r in rows) == summary['sent']
            assert summary['http_2xx'] + summary['http_429'] + summary['http_5xx'] + summary['transport_errors'] + summary['timeouts'] == summary['sent']
            assert sum(bool(r.get('sent_at')) and 200 <= (r.get('status') or 0) < 300 for r in rows) == summary['http_2xx']
            assert sum(bool(r.get('sent_at')) and r.get('status') == 429 for r in rows) == summary['http_429']
            assert sum(bool(r.get('sent_at')) and (r.get('status') or 0) >= 500 for r in rows) == summary['http_5xx']
            assert sum(bool(r.get('sent_at')) and (r.get('error') or r.get('timeout')) for r in rows) == summary['transport_errors'] + summary['timeouts']
            sent = [r for r in rows if r.get('sent_at')]
            assert sum(r['client_class'] == 'legitimate' for r in sent) == 600
            assert sum(r['client_class'] == 'abusive' for r in sent) == 2400
            duration = config['duration_ns'] / 1e9
            start = epoch(summary['started_at'])
            fidelity = {}
            schedule_residuals, latency_residuals = [], []
            for cls, target in (('legitimate', 20), ('abusive', 80)):
                selected = [r for r in sent if r['client_class'] == cls]
                actual = sum(0 <= epoch(r['sent_at']) - start < duration for r in selected) / duration
                lags = sorted(r['schedule_lag_ms'] for r in selected)
                p95_lag = lags[math.ceil(.95 * len(lags)) - 1]
                assert abs(actual / target - 1) <= .05, f'{policy}/{phase}: {cls} rate fidelity'
                assert p95_lag <= min(10, 1000 / target), f'{policy}/{phase}: {cls} p95 schedule lag'
                fidelity[cls] = {'target_rps': target, 'actual_wall_phase_rps': actual, 'p95_schedule_lag_ms': p95_lag}
            for r in sent:
                schedule_residuals.append(abs((epoch(r['sent_at']) - epoch(r['scheduled_at'])) * 1000 - r['schedule_lag_ms']))
                latency_residuals.append(abs((epoch(r['end_at']) - epoch(r['sent_at'])) * 1000 - r['latency_ms']))
            max_schedule_residual = max(schedule_residuals)
            max_latency_residual = max(latency_residuals)
            assert max_schedule_residual < 5 and max_latency_residual < 5, f'{policy}/{phase}: clock residual'
            deltas = analysis['counter_deltas']
            apis = [deltas['api1'], deltas['api2']]
            backend = deltas['backend']
            assert sum(x['requests'] for x in apis) == summary['sent']
            assert sum(x['rejected'] for x in apis) == summary['http_429']
            assert sum(x['backend_attempts'] for x in apis) == sum(r.get('limiter_decision') in ('allow', 'fail-open') for r in sent)
            assert sum(x['backend_confirmed_arrivals'] for x in apis) == sum(r.get('backend_arrival') == 'true' for r in sent)
            assert sum(x['backend_confirmed_arrivals'] for x in apis) == backend['arrivals']
            assert backend['arrivals'] == summary['backend_confirmed_arrivals']
            assert backend['arrivals'] == backend['success'] + backend['overload'] + backend['canceled']
            assert summary['http_2xx'] == backend['success']
            assert sum(x['limiter_errors'] for x in apis) == sum(x['fail_open'] + x['fail_closed'] for x in apis)
            assert sum(x['fail_open'] for x in apis) == sum(r.get('limiter_decision') == 'fail-open' for r in sent)
            assert sum(x['fail_closed'] for x in apis) == sum(r.get('limiter_decision') == 'fail-closed' for r in sent)
            image_ids = {item['ID'] for item in json.loads((case / 'images.json').read_text())}
            inspected_ids = {item['Id'] for item in json.loads((case / 'image-inspect.json').read_text())}
            assert image_ids == inspected_ids
            assert len([x for x in json.loads((case / 'images.json').read_text())]) >= 5
            assert (case / 'image-inspect.json').is_file()
            assert analysis['evidence']['summary_counts_match_trace'] is True
            if phase == 'healthy':
                assert sum(x['limiter_errors'] for x in apis) == 0
                assert backend['overload'] == 0
                assert summary['legitimate_successful'] == summary['legitimate_sent'] == 600
                assert summary['http_5xx'] == summary['transport_errors'] == summary['timeouts'] == 0
            else:
                expected_events = {'pause_requested', 'pause_completed', 'unpause_requested', 'unpause_completed'}
                events = [(line.split()[-1], epoch(line.split()[0])) for line in (case / 'outage-events.txt').read_text().splitlines()
                          if line.split() and line.split()[-1] in expected_events]
                assert [name for name, _ in events] == ['pause_requested', 'pause_completed', 'unpause_requested', 'unpause_completed']
                times = dict(events)
                assert times['pause_requested'] <= times['pause_completed'] < times['unpause_requested'] <= times['unpause_completed']
                assert 1.5 <= times['unpause_requested'] - times['pause_completed'] <= 2.5
                threshold = float((root / policy / 'recovery-p95-threshold-ms.txt').read_text())
                healthy_summary = json.loads((healthy / 'load/summary.json').read_text())
                p95 = healthy_summary['legitimate_success_latency']['p95_ms']
                assert math.isclose(threshold, max(1, 1.5 * p95), rel_tol=1e-7)
                recovery = analysis['outage']['recovery']
                assert recovery['status'] == 'observed' and recovery['stable_recovery_ms'] == 4000
                assert recovery['first_legitimate_success_after_unpause_ms'] != recovery['stable_recovery_ms']
                full_post_windows = math.floor((start + duration - times['unpause_completed']))
                assert full_post_windows >= 5
                if policy == 'open':
                    assert sum(x['fail_open'] for x in apis) > 0 and sum(x['fail_closed'] for x in apis) == 0
                else:
                    assert sum(x['fail_closed'] for x in apis) > 0 and sum(x['fail_open'] for x in apis) == 0
                phase_availability = {name: item['legitimate_availability'] for name, item in analysis['outage']['phases'].items()}
            phase_results[phase] = {
                'run_id': config['run_id'], 'scheduled': summary['scheduled'], 'sent': summary['sent'],
                'drops': summary['generator_dropped'], 'http_2xx': summary['http_2xx'], 'http_429': summary['http_429'],
                'http_5xx': summary['http_5xx'], 'legitimate_sent': summary['legitimate_sent'],
                'legitimate_successful': summary['legitimate_successful'], 'fidelity': fidelity,
                'max_schedule_clock_residual_ms': max_schedule_residual,
                'max_latency_clock_residual_ms': max_latency_residual,
                'backend': {k: backend[k] for k in ('arrivals', 'success', 'overload', 'canceled')},
                'api_limiter_errors': sum(x['limiter_errors'] for x in apis),
                'oracle_status': analysis['oracle']['status'],
            }
            if phase == 'outage':
                phase_results[phase].update({'recovery_threshold_ms': threshold, 'recovery': recovery,
                                             'availability_by_send_phase': phase_availability,
                                             'events_utc': analysis['outage']['events_utc'],
                                             'full_post_unpause_windows': full_post_windows})
        results.append({'policy': policy, 'cases': phase_results})
    return {'revision': '09b1249a08adf441062f8f6918b771b5cb8852e8', 'config': {
        'algorithm': 'fixed-window', 'Q': 20, 'W_ms': 1000, 'B': 20, 'r': 20,
        'api_instances': 2, 'legitimate_keys': 5, 'total_rps': 100, 'legitimate_rps': 20,
        'duration_seconds': 30, 'backend_capacity': 10, 'backend_service_time': '50ms',
        'pause_at_seconds': 4, 'pause_for_seconds': 2, 'recovery_threshold': '1.5x healthy legitimate-success p95',
        'recovery_window_ms': 1000, 'recovery_min_samples': 5, 'recovery_consecutive': 3,
    }, 'policies': results}


if __name__ == '__main__':
    result = check(Path(sys.argv[1]))
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    rendered = json.dumps(result, indent=2) + '\n'
    if output:
        output.write_text(rendered)
    else:
        print(rendered, end='')
