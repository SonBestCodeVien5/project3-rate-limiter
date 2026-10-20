"""Mocked coordinator lifecycle tests; no Docker or load is started."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('run_study', Path(__file__).with_name('run-study.py'))
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def manifest(root, standard_cells=42):
    runs, cells = [], []
    n = 0
    for c in range(standard_cells):
        cell = f'cell-{c}'
        cells.append({'id': cell, 'expected_repetitions': 3})
        for rep in range(1, 4):
            n += 1
            path = root / f'run-{n}' / 'custom-repeat-1'
            runs.append({'planned_run_id': f'r{n}', 'cell': cell, 'group': 'RQ1', 'repetition': str(rep),
                         'source_revision': 'abc', 'config': {'policy': {'fail_policy': 'closed'}},
                         'environment': {'X': str(n)}, 'command': ['runner', '--output', str(root / f'run-{n}')],
                         'invocation_id': f'inv-{n}', 'output_path': str(root / f'run-{n}'),
                         'result_path': str(path)})
    for rep in range(1, 4):
        for policy in ('open', 'closed'):
            root_path = root / f'outage-{policy}-{rep}'
            ids = [f'outage-{policy}-{rep}-healthy', f'outage-{policy}-{rep}-outage']
            cells.extend([{'id': x, 'expected_repetitions': 3} for x in ids])
            for phase, run_id in zip(('healthy', 'outage'), ids):
                n += 1
                runs.append({'planned_run_id': run_id, 'cell': f'outage-{policy}-{phase}', 'group': 'RQ5', 'repetition': str(rep),
                             'source_revision': 'abc', 'config': {'policy': {'fail_policy': policy}},
                             'environment': {'OUTAGE': policy}, 'command': ['runner', str(root_path)],
                             'invocation_id': f'outage-{policy}-r{rep}', 'output_path': str(root_path),
                             'result_path': str(root_path / policy / phase)})
    return {'clock_tolerance_ms': 5, 'cells': cells, 'runs': runs,
            'status': 'locked', 'execution_authorized': True, 'source_revision': 'abc',
            'runtime': {'redis_image': {'configured_reference': 'redis:pin', 'inspected_id': 'r', 'repo_digest': 'redis@sha256:r'},
                        'nginx_image': {'configured_reference': 'nginx:pin', 'inspected_id': 'n', 'repo_digest': 'nginx@sha256:n'}}}


class CoordinatorTest(unittest.TestCase):
    def setup_case(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        checkout = root / 'checkout'
        checkout.mkdir()
        planned = root / 'planned.json'
        planned.write_text(json.dumps(manifest(root)))
        out = root / 'coordinator'
        args = type('Args', (), {'manifest': planned, 'output': out, 'resume': False})
        return tmp, root, checkout, planned, out, args

    def test_manifest_v11_groups_126_standard_rows_and_six_outage_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            groups = mod.groups(manifest(Path(td))['runs'])
            self.assertEqual(len(groups), 132)
            self.assertEqual(sum(len(group) == 1 for group in groups), 126)
            self.assertEqual(sum(len(group) == 2 for group in groups), 6)

    def test_actual_v11_manifest_is_readable_but_draft_gate_blocks_execution(self):
        path = Path(__file__).resolve().parents[1] / 'docs/experiments/protocol-v1.1/manifest.json'
        if not path.exists():
            self.skipTest('protocol-v1.1 external fixture is absent from pinned tools checkout')
        data = json.loads(path.read_text())
        self.assertEqual((len(data['runs']), len(mod.groups(data['runs']))), (138, 132))
        self.assertEqual(mod.base_path(path, data['runs'][0]), (mod.ROOT / data['runs'][0]['output_path'] / 'custom-repeat-1').resolve())
        self.assertEqual(mod.base_path(path, data['runs'][-1]), (mod.ROOT / data['runs'][-1]['output_path'] / 'closed/outage').resolve())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkout = root / 'checkout'
            checkout.mkdir()
            data['execution_authorized'], data['status'] = False, 'draft'
            fixture = root / 'manifest.json'
            fixture.write_text(json.dumps(data))
            args = type('Args', (), {'manifest': fixture, 'output': root / 'out', 'resume': False})
            with patch.object(mod, 'ROOT', checkout), patch.object(mod.subprocess, 'run') as runner:
                self.assertEqual(mod.run(args), 2)
                runner.assert_not_called()

    def test_fixed_outage_analysis_archives_dynamic_files_and_keeps_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = 'artifacts/protocol-v1.1/outage-open-r1'
            case = root / rel / 'open/outage'
            case.mkdir(parents=True)
            policy = root / rel / 'open'
            (policy / 'recovery-p95-threshold-ms.txt').write_text('73.5\n')
            originals = {}
            commands = []
            for name in ('analysis.json', 'analysis.md', 'analyzer.log'):
                (case / name).write_text('dynamic ' + name)
                originals[name] = 'dynamic ' + name
                commands.append(['cp', '-p', f'{rel}/open/outage/{name}', f'{rel}/open/outage/{name.replace(".", ".dynamic-t07.", 1)}'])
            commands.append(['timeout', '20s', 'python3', 'scripts/analyze.py', f'{rel}/open/outage', '--recovery-p95-ms', '81.9048105', '--recovery-window-ms', '1000', '--recovery-min-samples', '5', '--recovery-consecutive', '3'])
            entry = {'output_path': rel, 'fixed_analysis_commands': commands, 'config': {'policy': {'fail_policy': 'open'}}}
            group = [entry]
            def fake_run(command, **kwargs):
                if command[0] == 'cp':
                    import shutil
                    shutil.copy2(command[2], command[3])
                else:
                    (case / 'analysis.json').write_text('fixed analysis')
                return type('Result', (), {'returncode': 0})()
            with patch.object(mod, 'ROOT', root), patch.object(mod.subprocess, 'run', side_effect=fake_run):
                result = mod.fixed_outage_analysis(root / 'manifest.json', group, root / rel)
            for name, content in originals.items():
                self.assertEqual((case / name.replace('.', '.dynamic-t07.', 1)).read_text(), content)
            self.assertEqual((case / 'analysis.json').read_text(), 'fixed analysis')
            self.assertEqual((policy / 'recovery-p95-threshold-ms.txt').read_text(), '73.5\n')
            self.assertEqual((policy / 'recovery-p95-threshold-ms.dynamic-t07.txt').read_text(), '73.5\n')
            self.assertEqual((case / 'fixed-recovery-p95-threshold-ms.txt').read_text(), '81.9048105\n')
            self.assertEqual(list(result['thresholds'].values()), ['81.9048105'])

    def test_outage_retry_is_pair_scoped_and_maps_accepted_paths(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        calls, checker_calls = [], 0
        class Result:
            returncode = 0
        def fake_run(command, **kwargs):
            nonlocal checker_calls
            if command[0] == 'runner':
                calls.append(command)
                Path(command[-1] if len(command) == 2 else command[2]).mkdir(parents=True, exist_ok=True)
                return Result()
            checker_calls += 1
            target = Path(command[command.index('--output') + 1])
            target.parent.mkdir(parents=True, exist_ok=True)
            run_id = command[command.index('--planned-run-id') + 1]
            # The first healthy check fails; the whole matching outage pair retries together.
            target.write_text(json.dumps({'valid': not (checker_calls == 127), 'stop_sequence': False, 'reasons': [], 'config_fingerprint': 'cfg', 'image_fingerprint': 'img'}))
            return Result()
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            rc = mod.run(args)
        self.assertEqual(rc, 0)
        records = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines()]
        outage_records = [row for row in records if row['invocation_id'] == 'outage-open-r1' and row['event'] == 'attempt_finished']
        self.assertEqual(len(outage_records), 2)
        self.assertEqual(outage_records[-1]['attempt'], 2)
        accepted = json.loads((out / 'manifest.json').read_text())['runs']
        outage_paths = [row['path'] for row in accepted if row['cell'].startswith('outage-open-') and row['repetition'] == '1']
        self.assertTrue(all('.attempt-2' in path for path in outage_paths))
        existing_calls = len(calls)
        resume_args = type('Args', (), {'manifest': planned, 'output': out, 'resume': True})
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(resume_args), 0)
        self.assertEqual(len(calls), existing_calls)
        Path(accepted[0]['path'], 'coordinator-quality-check.json').write_text('tampered')
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(resume_args), 2)
        self.assertEqual(len(calls), existing_calls)

    def test_no_overwrite_and_fatal_setup_stop(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        out.mkdir()
        (out / 'attempts.jsonl').write_text('')
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}):
            self.assertEqual(mod.run(args), 2)

    def test_cell_retry_budget_is_shared_across_repetitions_and_continues(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        runner_calls = []
        class Result:
            returncode = 0
        def fake_run(command, **kwargs):
            if command[0] == 'runner':
                runner_calls.append(command)
                Path(command[2] if len(command) > 2 else command[-1]).mkdir(parents=True, exist_ok=True)
                return Result()
            target = Path(command[command.index('--output') + 1])
            target.parent.mkdir(parents=True, exist_ok=True)
            run_id = command[command.index('--planned-run-id') + 1]
            target.write_text(json.dumps({'valid': not run_id.startswith('r1'), 'stop_sequence': False, 'reasons': [], 'config_fingerprint': 'cfg', 'image_fingerprint': 'img'}))
            return Result()
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(args), 1)
        rows = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines()]
        self.assertEqual(sum(row['invocation_id'] == 'inv-1' and row['event'] == 'attempt_finished' for row in rows), 3)
        self.assertFalse(any(row['invocation_id'] in ('inv-2', 'inv-3') for row in rows))
        self.assertTrue(any(row['invocation_id'] == 'inv-4' and row['event'] == 'attempt_finished' and row['accepted'] for row in rows))

    def test_runner_setup_failure_stops_remaining_sequence(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        calls = []
        def fake_run(command, **kwargs):
            calls.append(command)
            raise FileNotFoundError('mock setup failure')
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(args), 2)
        records = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines()]
        finished = [row for row in records if row['event'] == 'attempt_finished']
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]['runner_exit_code'], 127)
        self.assertEqual(len(calls), 1)

    def test_preflight_checks_local_images_and_fresh_clock_without_pulling(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkout = root / 'checkout'
            checkout.mkdir()
            data = manifest(root)
            observer = root / 'observer'
            calls = []
            def check_output(command, **kwargs):
                if command[:2] == ['git', 'rev-parse']:
                    return 'abc\n'
                if command[:2] == ['git', 'status']:
                    return ''
                if command[:3] == ['docker', 'image', 'inspect']:
                    key = 'redis_image' if 'redis:' in command[-1] else 'nginx_image'
                    pin = data['runtime'][key]
                    return json.dumps([{'Id': pin['inspected_id'], 'RepoDigests': [pin['repo_digest']]}])
                if command[:3] == ['docker', 'ps', '-aq']:
                    return ''
                self.fail(f'unexpected command: {command}')
            def run_command(command, **kwargs):
                calls.append(command)
                dest = Path(command[command.index('--output') + 1])
                dest.mkdir(parents=True)
                (dest / 'summary.json').write_text(json.dumps({'duration_seconds': 90, 'elapsed_monotonic_seconds': 90, 'clock_steps_above_5ms': []}))
                return type('Result', (), {'returncode': 0})()
            with patch.object(mod, 'ROOT', checkout), patch.object(mod.subprocess, 'check_output', side_effect=check_output), patch.object(mod.subprocess, 'run', side_effect=run_command):
                result = mod.preflight(data, root / 'manifest.json', observer)
            self.assertEqual(result['containers'], set())
            self.assertEqual(len(calls), 1)
            self.assertNotIn('pull', calls[0])

    def test_resume_after_interrupted_start_preserves_path_and_uses_next_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkout = root / 'checkout'
            checkout.mkdir()
            output = root / 'coordinator'
            planned = root / 'planned.json'
            raw = manifest(root, standard_cells=1)
            raw['runs'] = raw['runs'][:1]
            raw['cells'] = raw['cells'][:1]
            planned.write_text(json.dumps(raw))
            original = root / 'artifacts/protocol-v1.1/cell-0'
            original.mkdir(parents=True)
            ledger = output / 'attempts.jsonl'
            output.mkdir()
            ledger.write_text(json.dumps({'event': 'attempt_started', 'invocation_id': 'inv-1', 'planned_run_ids': ['r1'],
                                          'retry_budget_key': 'cell:cell-0', 'attempt': 1, 'run_path': str(original),
                                          'source_revision': 'abc', 'config': [raw['runs'][0]['config']],
                                          'manifest_sha256': mod.sha256(planned)}) + '\n')
            args = type('Args', (), {'manifest': planned, 'output': output, 'resume': True})
            used = []
            class Result:
                returncode = 0
            def fake_run(command, **kwargs):
                if command[0] == 'runner':
                    used.append(command[2])
                    Path(command[2]).mkdir(parents=True, exist_ok=True)
                    return Result()
                target = Path(command[command.index('--output') + 1])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps({'valid': True, 'stop_sequence': False, 'reasons': [], 'config_fingerprint': 'cfg', 'image_fingerprint': 'img'}))
                return Result()
            with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
                self.assertEqual(mod.run(args), 0)
            self.assertEqual(len(used), 1)
            self.assertIn('.attempt-2', used[0])
            self.assertTrue(original.exists())

    def test_outage_healthy_gate_failure_retries_pair_without_stopping_sequence(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        calls = []
        def fake_run(command, **kwargs):
            if command[0] == 'runner':
                calls.append(command)
                Path(command[-1] if len(command) == 2 else command[2]).mkdir(parents=True, exist_ok=True)
                rc = 1 if 'outage-open-1' in command[-1] else 0
                return type('Result', (), {'returncode': rc})()
            target = Path(command[command.index('--output') + 1])
            target.parent.mkdir(parents=True, exist_ok=True)
            run_id = command[command.index('--planned-run-id') + 1]
            valid = not run_id.startswith('outage-open-1-healthy')
            target.write_text(json.dumps({'valid': valid, 'stop_sequence': False, 'reasons': [], 'config_fingerprint': 'cfg', 'image_fingerprint': 'img'}))
            return type('Result', (), {'returncode': 0})()
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(args), 1)
        rows = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines() if json.loads(line).get('event') == 'attempt_finished']
        pair = [row for row in rows if row['invocation_id'] == 'outage-open-r1']
        self.assertEqual(len(pair), 3)
        self.assertTrue(any('healthy_gate_failed_before_outage' in r.get('reasons', []) for row in pair for r in row['checks'].values()))
        self.assertTrue(any(row['invocation_id'] == 'outage-closed-r1' and row['accepted'] for row in rows))

    def test_boottime_gap_over_tolerance_stops_after_one_invocation(self):
        tmp, root, checkout, planned, out, args = self.setup_case()
        self.addCleanup(tmp.cleanup)
        data = manifest(root, standard_cells=1)
        data['runs'], data['cells'] = data['runs'][:1], data['cells'][:1]
        planned.write_text(json.dumps(data))
        calls = []
        def fake_run(command, **kwargs):
            if command[0] == 'runner':
                calls.append(command)
                Path(command[2]).mkdir(parents=True, exist_ok=True)
                return type('Result', (), {'returncode': 0})()
            target = Path(command[command.index('--output') + 1])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({'valid': True, 'stop_sequence': False, 'reasons': [], 'config_fingerprint': 'cfg', 'image_fingerprint': 'img'}))
            return type('Result', (), {'returncode': 0})()
        with patch.object(mod, 'ROOT', checkout), patch.object(mod, 'CHECKER', root / 'checker'), patch.object(mod, 'preflight', return_value={'containers': set(), 'summary': {}}), patch.object(mod, 'check_cleanup'), patch.object(mod, 'suspend_gap_ms', side_effect=[20.0, 26.0]), patch.object(mod.subprocess, 'run', side_effect=fake_run):
            self.assertEqual(mod.run(args), 2)
        finished = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines() if json.loads(line).get('event') == 'attempt_finished']
        self.assertEqual(len(calls), 1)
        self.assertAlmostEqual(finished[0]['boottime_minus_monotonic_delta_ms'], 6.0)
        self.assertIn('guest_suspend_detected', finished[0]['setup_error'])


if __name__ == '__main__':
    unittest.main()
