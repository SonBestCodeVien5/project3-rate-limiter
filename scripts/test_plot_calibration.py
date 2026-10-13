import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('plot_calibration', Path(__file__).with_name('plot-calibration.py'))
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


class PlotValidationTest(unittest.TestCase):
    def row(self, cell='selected', **changes):
        row = dict(cell=cell, profile='mixed', mode='redis', legitimate_successful=8, backend_overload=3, quality_flags='', oracle='inconclusive', phases=[dict(client_class='legitimate', sent=10, valid=True), dict(client_class='abusive', sent=90, valid=True)])
        row.update(changes)
        return row

    def test_explicit_selection_and_flags_preserved(self):
        rows = [self.row('unselected'), self.row(quality_flags='clock_wall_monotonic_discontinuity', limiter_errors=2)]
        points = plot.prepare_points(rows, [dict(cell='selected', mode='redis')])
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]['legitimate_success_fraction'], .8)
        self.assertEqual(points[0]['backend_overload'], 3)
        self.assertIn('clock_wall_monotonic_discontinuity', points[0]['quality_flags'])
        self.assertIn('limiter_errors_observed', points[0]['quality_flags'])
        self.assertEqual(points[0]['oracle_status'], 'inconclusive')

    def test_missing_selected_run_remains_gap(self):
        points = plot.prepare_points([], [dict(cell='missing', mode='none')])
        self.assertIsNone(points[0]['legitimate_success_fraction'])
        self.assertIsNone(points[0]['backend_overload'])
        self.assertIn('missing_selected_run', points[0]['quality_flags'])

    def test_missing_or_bad_numbers_are_not_zero(self):
        for row in (self.row(phases=[]), self.row(legitimate_successful=20, backend_overload=float('nan'))):
            point = plot.prepare_points([row], [dict(cell='selected', mode='redis')])[0]
            self.assertIsNone(point['legitimate_success_fraction'])
            self.assertIn('missing_legitimate_success_fraction', point['quality_flags'])
        self.assertIsNone(point['backend_overload'])

    def test_wrong_mode_profile_and_duplicates_refused(self):
        entry = dict(cell='selected', mode='redis')
        for rows, entries in (([self.row(mode='local')], [entry]), ([self.row(profile='normal')], [entry]), ([self.row(), self.row()], [entry]), ([self.row()], [entry, entry])):
            with self.assertRaises(ValueError):
                plot.prepare_points(rows, entries)


if __name__ == '__main__':
    unittest.main()
