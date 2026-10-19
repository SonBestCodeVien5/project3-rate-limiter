import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('report_study', Path(__file__).with_name('report-study.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fixture(self, name, p95=10, drops=0):
        case = self.root / name / 'case-repeat-1'
        case.mkdir(parents=True)
        def write(relative, value):
            path = case / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        policy = dict(mode='redis', algorithm='fixed-window', fail_policy='closed', limit=20, window_ms=1000, capacity=20, rate_per_sec=20, state_reset=True, namespace=name)
        summary = {key: 0 for key in report.SUMMARY_METRICS}
        summary.update(run_id='case-repeat-1', sent=1, scheduled=1+drops, generator_dropped=drops, canceled=False, legitimate_successful=1, legitimate_success_latency=dict(p50_ms=5, p95_ms=p95, p99_ms=20))
        write('load/summary.json', summary)
        write('policy.json', policy)
        write('load/metadata.json', dict(config=dict(run_id='case-repeat-1', mode_label='redis', algorithm_label='fixed-window', fail_policy_label='closed', profile='mixed', duration_ns=1000, rps=1, legitimate_rps=1, legitimate_clients=5, max_inflight=200, timeout_ns=100, max_schedule_lag_ns=10), workload_version=2, git_revision='abc', git_status_porcelain='', go_version='go', os='linux', arch='amd64', cpu_count=12, gomaxprocs=12, hostname='host'))
        write('analysis.json', dict(run_id='case-repeat-1', policy=policy, oracle=dict(status='inconclusive'), evidence=dict(summary_counts_match_trace=True, trace_has_unknown_decisions=False), counter_deltas=dict(api1=dict(limiter_errors=0), backend=dict(arrivals=1, overload=0)), redis_resources=None))
        write('compose-resolved.json', dict(services=dict(api1=dict(environment=dict(MODE='redis', ALGORITHM='fixed-window', NAMESPACE=name)), backend=dict(environment=dict(BACKEND_CAPACITY='4', BACKEND_SERVICE_TIME='50ms')), nginx={}, redis={})))
        write('images.json', [dict(ContainerName='lab-'+key+'-1', ID=key, Platform='amd64') for key in ('api1', 'backend', 'nginx', 'redis')])
        (case.parent / 'git-revision.txt').write_text('abc')
        (case.parent / 'git-status.txt').write_text('')
        (case / 'base-image-digests.txt').write_text('digests')
        (case / 'topology').mkdir()
        (case / 'topology/nginx.conf').write_text('upstream api1')
        rows = [dict(request_id='1', sent_at='2026-10-13T00:00:00.001+00:00', scheduled_at='2026-10-13T00:00:00+00:00', end_at='2026-10-13T00:00:00.002+00:00', latency_ms=1, schedule_lag_ms=1, limiter_decision='allow')]
        rows += [dict(request_id='drop-'+str(i)) for i in range(drops)]
        (case / 'load/requests.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
        return dict(path=str(case), cell='fw', group='RQ1', repetition=name)

    def test_individual_percentiles_and_fw_inconclusive(self):
        rows = [report.read_run(self.fixture('a', 10), self.root, 5), report.read_run(self.fixture('b', 30), self.root, 5)]
        self.assertTrue(all(row['tooling_validity'] == 'usable' for row in rows))
        result = report.summarize(rows, [dict(id='fw', expected_repetitions=2)])[0]
        self.assertEqual(result['legitimate_p95_ms_run_median'], 20)
        self.assertNotIn('pooled_p95', result)
        self.assertEqual(result['aggregation_status'], 'complete_same_config')

    def test_absent_redis_resource_sample_is_usable(self):
        entry = self.fixture('no-redis-sampler')
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(dict(clock_tolerance_ms=5, cells=[dict(id='fw', expected_repetitions=1)], runs=[entry])))
        rows, _ = report.export(manifest, self.root / 'output')
        self.assertEqual(rows[0]['tooling_validity'], 'usable')
        self.assertIsNone(rows[0]['redis_average_cpu_cores'])
        analysis_path = Path(entry['path'], 'analysis.json')
        analysis = json.loads(analysis_path.read_text())
        analysis['redis_resources'] = []
        analysis_path.write_text(json.dumps(analysis))
        malformed = report.read_run(entry, self.root, 5)
        self.assertEqual(malformed['tooling_validity'], 'invalid')
        self.assertIn('malformed_redis_resources', malformed['quality_flags'])

    def test_missing_evidence_and_invalid_rows_retained(self):
        entries = [self.fixture('a'), self.fixture('b', drops=1)]
        Path(entries[0]['path'], 'images.json').unlink()
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(dict(clock_tolerance_ms=5, cells=[dict(id='fw', expected_repetitions=2)], runs=entries)))
        rows, cells = report.export(manifest, self.root / 'output')
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row['tooling_validity'] == 'invalid' for row in rows))
        self.assertIn('generator_drops', rows[1]['quality_flags'])
        self.assertIn('invalid_run_evidence', cells[0]['aggregation_status'])
        self.assertNotIn('legitimate_p95_ms_run_median', cells[0])
        self.assertIn('not a pooled percentile', (self.root / 'output/report.md').read_text())

    def test_policy_mismatch_and_missing_repetitions(self):
        a, b = self.fixture('a'), self.fixture('b')
        path = Path(b['path'], 'policy.json')
        policy = json.loads(path.read_text()); policy['limit'] = 21; path.write_text(json.dumps(policy))
        analysis_path = Path(b['path'], 'analysis.json')
        analysis = json.loads(analysis_path.read_text()); analysis['policy'] = policy; analysis_path.write_text(json.dumps(analysis))
        rows = [report.read_run(entry, self.root, 5) for entry in (a, b)]
        cell = report.summarize(rows, [dict(id='fw', expected_repetitions=3)])[0]
        self.assertIn('incompatible_config', cell['aggregation_status'])
        self.assertIn('repetition_count_or_labels', cell['aggregation_status'])

    def test_client_clock_discontinuity_flag(self):
        entry = self.fixture('a')
        path = Path(entry['path'], 'load/requests.jsonl')
        row = json.loads(path.read_text()); row['sent_at'] = '2026-10-13T00:00:01+00:00'; path.write_text(json.dumps(row)+'\n')
        result = report.read_run(entry, self.root, 5)
        self.assertIn('client_clock_discontinuity_suspected', result['quality_flags'])
        self.assertEqual(result['tooling_validity'], 'invalid')

    def test_image_content_identity_requires_matching_recorded_ids(self):
        entries = [self.fixture('image-a'), self.fixture('image-b')]
        for index, entry in enumerate(entries):
            case = Path(entry['path'])
            image_path = case / 'images.json'
            images = json.loads(image_path.read_text())
            for image in images:
                image['ID'] += str(index)
            image_path.write_text(json.dumps(images))
            inspect = [dict(Id=image['ID'], RootFS=dict(Type='layers', Layers=['sha256:'+'a'*64]), Config=dict(Env=['ROLE=app'], Entrypoint=['/app']), Os='linux', Architecture='amd64') for image in images]
            (case / 'image-inspect.json').write_text(json.dumps(inspect))
        def result():
            rows = [report.read_run(entry, self.root, 5) for entry in entries]
            return report.summarize(rows, [dict(id='fw', expected_repetitions=2)])[0]
        self.assertEqual(result()['aggregation_status'], 'complete_same_config')
        inspect_path = Path(entries[1]['path'], 'image-inspect.json')
        inspect = json.loads(inspect_path.read_text())
        inspect[0]['RootFS']['Layers'][0] = 'sha256:'+'b'*64
        inspect_path.write_text(json.dumps(inspect))
        self.assertIn('incompatible_config', result()['aggregation_status'])
        inspect[0]['RootFS']['Layers'][0] = 'sha256:'+'a'*64
        inspect[0]['Config']['Env'] = ['ROLE=other']
        inspect_path.write_text(json.dumps(inspect))
        self.assertIn('incompatible_config', result()['aggregation_status'])
        inspect[0]['Config']['Env'] = ['ROLE=app']
        inspect[0]['Id'] = 'forged'
        inspect_path.write_text(json.dumps(inspect))
        self.assertIn('invalid_run_evidence', result()['aggregation_status'])
        for entry in entries:
            Path(entry['path'], 'image-inspect.json').unlink()
        self.assertIn('incompatible_config', result()['aggregation_status'])
        inspect_path.write_text('malformed')
        row = report.read_run(entries[1], self.root, 5)
        self.assertIn('missing_or_malformed:image-inspect.json', row['quality_flags'])

    def test_clock_jump_during_final_response_is_not_missed(self):
        entry = self.fixture('drain')
        path = Path(entry['path'], 'load/requests.jsonl')
        row = json.loads(path.read_text()); row['end_at'] = '2026-10-13T00:00:01.002+00:00'; path.write_text(json.dumps(row)+'\n')
        result = report.read_run(entry, self.root, 5)
        self.assertIn('client_clock_discontinuity_suspected', result['quality_flags'])
        self.assertEqual(result['tooling_validity'], 'invalid')


if __name__ == '__main__':
    unittest.main()
