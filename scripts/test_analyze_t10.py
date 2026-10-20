import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('analyze_t10',Path(__file__).with_name('analyze-t10.py'))
tool=importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)


class T10Tests(unittest.TestCase):
    def test_per_run_median_range_and_missing_metrics(self):
        rows=[{'x':str(x)} for x in (1,9,3)]
        self.assertEqual(tool.stats(rows,'x'),(3,1,9))
        self.assertIsNone(tool.stats(rows,'missing'))

    def test_locked_coverage_contrasts_and_fail_closed_provenance(self):
        locked_path=Path(__file__).parents[1]/'docs/experiments/protocol-v1.2/manifest.json'
        manifest=json.loads(locked_path.read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); runs_path=root/'runs.csv'; result_path=root/'result.json'
            entries=[]; row_data=[]
            for plan in manifest['runs']:
                entries.append(dict(cell=plan['cell'],repetition=plan['repetition'],planned_run_id=plan['planned_run_id'],group=plan['group'],source_revision=tool.SOURCE_REVISION,raw_checksums={'analysis.json':'a','load/summary.json':'b','load/metadata.json':'c'},image_fingerprint='same'))
                row_data.append(dict(group=plan['group'],cell=plan['cell'],repetition=plan['repetition'],run_id='custom-repeat-1',tooling_validity='usable',fingerprint='same',oracle_status='inconclusive',backend_arrivals='1',backend_overload='0'))
            result_path.write_text(json.dumps(dict(source_revision=tool.SOURCE_REVISION,runs=entries)))
            with runs_path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(row_data[0]));writer.writeheader();writer.writerows(row_data)
            _,rows,cells=tool.load_export(runs_path,locked_path,result_path,check_pins=False)
            self.assertEqual((len(rows),len(cells)),(138,46))

            altered=json.loads(json.dumps(manifest))
            next(c for c in altered['cells'] if c['id']=='normal-local-fw')['topology']['backend_capacity']=99
            altered_path=root/'altered.json';altered_path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,'uncontrolled contrast'):
                tool.load_export(runs_path,altered_path,result_path,check_pins=False)

            altered=json.loads(json.dumps(manifest))
            next(c for c in altered['cells'] if c['id']=='normal-none')['topology']['backend_capacity']=99
            altered_path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,'uncontrolled contrast no-local-redis: normal-none,normal-local-fw,normal-redis-fw'):
                tool.load_export(runs_path,altered_path,result_path,check_pins=False)

            entries[0]['planned_run_id'],entries[1]['planned_run_id']=entries[1]['planned_run_id'],entries[0]['planned_run_id']
            result_path.write_text(json.dumps(dict(source_revision=tool.SOURCE_REVISION,runs=entries)))
            with self.assertRaisesRegex(ValueError,'wrong cell/repetition/group'):
                tool.load_export(runs_path,locked_path,result_path,check_pins=False)

            with self.assertRaisesRegex(ValueError,'pinned input checksum mismatch'):
                tool.load_export(runs_path,locked_path,result_path,check_pins=True)

    def test_baseline_cell_is_included_in_report_table(self):
        self.assertEqual(tool.profile_cell_ids('mixed','none'),['mixed-none'])
        row={'oracle_status':'not_applicable','legitimate_goodput_per_second':'1575',
             'legitimate_p50_ms':'50','legitimate_p95_ms':'55','legitimate_p99_ms':'60',
             'api_allowed':'0','api_rejected':'0','oracle_violations':'0',
             'oracle_overshoot_lower_bound':'0'}
        rendered=tool.rq1_cell_row({'mixed-none':[row]},'mixed-none')
        self.assertIn('| mixed-none | 1575.000 (1575.000–1575.000) |',rendered)
        self.assertIn('| không áp dụng | — | — |',rendered)

    def test_hash_mutation_and_existing_output_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); path=root/'input';path.write_text('locked')
            expected=hashlib.sha256(b'locked').hexdigest()
            tool.check_hash(path,expected,'fixture')
            path.write_text('mutated')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                tool.check_hash(path,expected,'fixture')
            existing=root/'existing';existing.mkdir();sentinel=existing/'keep';sentinel.write_text('unchanged')
            with self.assertRaises(FileExistsError): tool.create_output(existing)
            self.assertEqual(sentinel.read_text(),'unchanged')

    def test_archive_locator_requires_exact_content_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); case=root/'raw/artifacts/protocol-v1.1/plan/custom-repeat-1'
            case.mkdir(parents=True); analysis=case/'analysis.json'; analysis.write_text('{"run":"p1-1"}')
            entry={'planned_run_id':'p1-1','path':'/old/artifacts/protocol-v1.1/plan/custom-repeat-1',
                   'raw_checksums':{'analysis.json':hashlib.sha256(analysis.read_bytes()).hexdigest()}}
            source,found=tool.locate_case(entry,{'v1.1':root,'v1.2':root,'v1.3':root})
            self.assertEqual((source,found),('v1.1',case))
            analysis.write_text('{"run":"mutated"}')
            with self.assertRaisesRegex(ValueError,'path/hash mismatch'):
                tool.locate_case(entry,{'v1.1':root,'v1.2':root,'v1.3':root})


if __name__=='__main__': unittest.main()
