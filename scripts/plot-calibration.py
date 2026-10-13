#!/usr/bin/env python3
"""Plot explicitly selected calibration runs offline; matplotlib is optional."""
import argparse
import json
import math
from pathlib import Path

MODES = ('none', 'local', 'redis')


def number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def prepare_points(rows, entries):
    if not isinstance(rows, list) or not isinstance(entries, list) or not entries:
        raise ValueError('source rows and explicit nonempty entries must be arrays')
    if any(not isinstance(row, dict) for row in rows) or any(not isinstance(entry, dict) or not isinstance(entry.get('cell'), str) or not entry['cell'] or entry.get('mode') not in MODES for entry in entries):
        raise ValueError('rows must be objects; entries require nonempty cell and valid mode')
    cells = [entry['cell'] for entry in entries]
    if len(set(cells)) != len(cells):
        raise ValueError('manifest cell selections must be unique')
    if any(entry['mode'] not in MODES for entry in entries):
        raise ValueError('entry mode must be none/local/redis')
    points = []
    for entry in entries:
        matches = [row for row in rows if row.get('cell') == entry['cell']]
        if len(matches) > 1:
            raise ValueError('duplicate source cell: ' + entry['cell'])
        row = matches[0] if matches else {}
        flags = [flag for flag in str(row.get('quality_flags') or '').split(';') if flag]
        if not row:
            flags.append('missing_selected_run')
        elif row.get('mode') != entry['mode'] or row.get('profile') != 'mixed':
            raise ValueError('selected cell must be mixed with matching mode: ' + entry['cell'])
        if row.get('tooling_validity') == 'invalid':
            flags.append('tooling_invalid')
        for field in ('limiter_errors', 'drops', 'generator_dropped', 'transport_errors', 'timeouts'):
            if number(row.get(field)) and row[field] > 0:
                flags.append(field + '_observed')
        phases = row.get('phases', [])
        legitimate = [phase for phase in phases if phase.get('client_class') == 'legitimate']
        if any(phase.get('valid') is not True for phase in phases):
            flags.append('phase_fidelity_unverified')
        denominator = sum(phase['sent'] for phase in legitimate) if legitimate and all(number(phase.get('sent')) and phase['sent'] >= 0 for phase in legitimate) else None
        successful = row.get('legitimate_successful')
        fraction = successful / denominator if number(successful) and denominator and 0 <= successful <= denominator else None
        if fraction is None:
            flags.append('missing_legitimate_success_fraction')
        overload = row.get('backend_overload')
        if not number(overload) or overload < 0:
            overload = None
            flags.append('missing_backend_overload')
        # shortcut: calibration quality fields are trusted, use trace validation/exporter for formal results.
        points.append(dict(cell=entry['cell'], mode=entry['mode'], legitimate_success_fraction=fraction, legitimate_sent=denominator, backend_overload=overload, quality_flags=sorted(set(flags)), oracle_status=row.get('oracle', 'missing')))
    return points


def read_manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text())
    source = (path.parent / manifest['source']).resolve()
    rows = json.loads(source.read_text())
    return prepare_points(rows, manifest['entries'])


def plot(points, output):
    # Import only when drawing, never during validation or tests.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError as error:
        raise SystemExit('Offline plotting requires matplotlib; no dependency was installed. Use --validate-only first.') from error
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    figure, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    metrics = [('legitimate_success_fraction', 'Legitimate 2xx / legitimate sent'), ('backend_overload', 'Backend overload count (counter delta)')]
    colors = {'none': '#586273', 'local': '#d48720', 'redis': '#187e86'}
    for axis, (metric, label) in zip(axes, metrics):
        for mode_index, mode in enumerate(MODES):
            selected = [point for point in points if point['mode'] == mode]
            for index, point in enumerate(selected):
                offset = (index - (len(selected) - 1) / 2) * .09
                x = mode_index + offset
                value = point[metric]
                if value is None:
                    axis.text(x, -.08 - index * .055, 'gap: ' + str(points.index(point) + 1), transform=axis.get_xaxis_transform(), ha='center', fontsize=8, color='#b3261e')
                    continue
                flagged = bool(point['quality_flags'])
                axis.scatter(x, value, marker='x' if flagged else 'o', color='#b3261e' if flagged else colors[mode], s=55, zorder=3)
                axis.annotate(str(points.index(point) + 1), (x, value), xytext=(4, 5), textcoords='offset points', fontsize=8)
        axis.set_xticks(range(3), ['No limiter', 'Local', 'Redis'])
        axis.set_ylabel(label)
        axis.grid(axis='y', alpha=.25)
        axis.set_xlim(-.5, 2.5)
        if metric == 'legitimate_success_fraction':
            axis.set_ylim(0, 1.1)
        else:
            axis.set_ylim(bottom=0)
    figure.suptitle('Pilot — not formal benchmark')
    figure.legend(handles=[Line2D([], [], marker='o', linestyle='', color='#586273', label='No reported quality flag'), Line2D([], [], marker='x', linestyle='', color='#b3261e', label='Quality flagged; inspect sidecar')], loc='lower center', bbox_to_anchor=(.5, .055), ncol=2)
    figure.text(.5, .015, 'Individual selected runs only. Numbers identify entries in points.json. Missing metrics are gaps. No pooled percentiles or significance claims.', ha='center', fontsize=8)
    figure.tight_layout(rect=(0, .15, 1, .94))
    figure.savefig(output / 'calibration.png', dpi=180)
    figure.savefig(output / 'calibration.svg')
    plt.close(figure)
    (output / 'points.json').write_text(json.dumps(points, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='JSON: source runs.json and explicit entries [{cell, mode}]')
    parser.add_argument('--output', help='new output directory for PNG, SVG and points.json')
    parser.add_argument('--validate-only', action='store_true', help='print selected points without importing matplotlib')
    args = parser.parse_args()
    points = read_manifest(args.manifest)
    if args.validate_only:
        print(json.dumps(points, indent=2))
    elif args.output:
        plot(points, args.output)
    else:
        parser.error('--output or --validate-only is required')
