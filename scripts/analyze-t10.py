#!/usr/bin/env python3
"""Validate and summarize the locked T09 export; all inputs are offline."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime
from pathlib import Path
from statistics import median

METRICS = ('legitimate_goodput_per_second', 'legitimate_p95_ms', 'legitimate_p99_ms',
           'backend_arrivals', 'backend_overload', 'http_429', 'http_5xx',
           'legitimate_p50_ms','backend_success','backend_canceled','http_timeouts',
           'api_allowed','api_rejected','oracle_violations','oracle_overshoot_lower_bound',
           'redis_average_cpu_cores','redis_memory_bytes_first','redis_memory_bytes_last',
           'redis_network_input_bytes_delta','redis_network_input_bytes_per_second',
           'redis_network_output_bytes_delta','redis_network_output_bytes_per_second',
           'redis_network_sample_interval_s','redis_network_sample_count','outage_stable_recovery_ms','outage_first_success_ms',
           'outage_before_availability','outage_pausing_availability','outage_paused_availability',
           'outage_unpausing_availability','outage_after_availability','burst_base_p95_ms','burst_peak_p95_ms')
PINS = {
    'runs_csv': 'f0392733923dc050fc6cf655f47c75e8876051b50e6f21bbf0e34d9b6e715c59',
    'result_manifest': 'd6e74897868bef82750f98cdc0b82025d563ab492c58fa311b5c185fdedcdaf3',
    'locked_manifest': '8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e',
    'v12_archive': 'ec67b58202c14027ded4f411516dcd5979052d5e384a12ba8f8511a712e06f8d',
    'v13_archive': 'c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c',
    'v11_archive': 'e7122b897a9af2036e09cc178835060cbdaaf9f7c22a7818b5ad6ee8a3fa8ce0',
    'v11_ledger': 'bd6c89ce44907d1d8ec72a7f7fe4c0cca03f0afaaf34b2347deab43fa2c29a16',
    'v12_ledger': 'fe0f672cafa0d9805149e6eea8b1dd1364e4d0815ef123d707690b4a55ef3969',
    'exporter': '391c53239e1a4191505f213df30d5924a5c47dec0af15d537c74dd7f2c9106c5',
    'v11_bundle_sums': '4860855eaca07ff033c2bd0b4607f0da77c1e68fa0538b8587cb84408dfcc292',
    'v12_bundle_sums': 'be7a09a74d9b51e1b437fae53a31cebbb773dd58ae5d433b9302274751932f6c',
    'v13_bundle_sums': 'd37744967d9fa5527fceda68c26931b03155a08abc3250e24d7f392876c17182',
}
SOURCE_REVISION = '0291a80fb404fea0eafee8c3431acc3631bb423e'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_export(runs_path, manifest_path, result_manifest_path, check_pins=True):
    manifest = json.loads(Path(manifest_path).read_text())
    result_manifest = json.loads(Path(result_manifest_path).read_text())
    if check_pins:
        for name, path in (('runs_csv', runs_path), ('result_manifest', result_manifest_path), ('locked_manifest', manifest_path)):
            if sha(path) != PINS[name]:
                raise ValueError('pinned input checksum mismatch: ' + name)
        if manifest.get('source_revision') != SOURCE_REVISION or result_manifest.get('source_revision') != SOURCE_REVISION:
            raise ValueError('measurement source revision mismatch')
    with Path(runs_path).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    planned = {cell['id']: cell['expected_repetitions'] for cell in manifest['cells']}
    if len(rows) != manifest['planned_run_count'] or len(planned) != manifest['planned_cell_count']:
        raise ValueError('export/manifest planned counts do not match locked protocol')
    by_cell = {cell: [row for row in rows if row['cell'] == cell] for cell in planned}
    if any(len(by_cell[cell]) != expected for cell, expected in planned.items()):
        raise ValueError('planned repetition completeness failed')
    if any(row['tooling_validity'] != 'usable' for row in rows):
        raise ValueError('invalid tooling rows are present; analysis fails closed')
    for cell, selected in by_cell.items():
        if len({row['repetition'] for row in selected}) != planned[cell] or len({row['fingerprint'] for row in selected}) != 1:
            raise ValueError('within-cell repetition/configuration mismatch: ' + cell)
    entries = result_manifest.get('runs', [])
    locked_runs={x['planned_run_id']:x for x in manifest['runs']}
    planned_by_pair = {(entry['cell'], str(entry['repetition'])): entry for entry in entries}
    row_pairs = [(row['cell'], row['repetition']) for row in rows]
    if len(entries) != len(rows) or len(planned_by_pair) != len(entries) or set(row_pairs) != set(planned_by_pair):
        raise ValueError('derived manifest planned IDs/repetitions do not match export')
    if len({entry['planned_run_id'] for entry in entries}) != len(entries):
        raise ValueError('duplicate planned run ID in derived manifest')
    if {entry['planned_run_id'] for entry in entries} != {run['planned_run_id'] for run in manifest['runs']}:
        raise ValueError('derived manifest planned run ID coverage mismatch')
    for entry in entries:
        lock=locked_runs[entry['planned_run_id']]
        row=next(r for r in rows if r['cell']==entry['cell'] and r['repetition']==str(entry['repetition']))
        if (entry['cell'],str(entry['repetition']),entry['group'])!=(lock['cell'],str(lock['repetition']),lock['group']) or row['group']!=entry['group']:
            raise ValueError('planned run ID mapped to wrong cell/repetition/group')
        if not all(k in entry.get('raw_checksums',{}) for k in ('analysis.json','load/summary.json','load/metadata.json')):
            raise ValueError('derived run provenance incomplete: '+entry['planned_run_id'])
    # Match every requested contrast across all configuration fields except the intended factor.
    cells = {cell['id']: cell for cell in manifest['cells']}
    def signature(cell, ignored):
        item = json.loads(json.dumps(cells[cell]))
        item.pop('id',None)
        for section, key in ignored:
            item[section].pop(key, None)
        return item
    comparisons=[]
    for profile in ('normal','mixed','burst'):
        for mode in ('none','local','redis'):
            fw,tb=f'{profile}-{mode}-fw',f'{profile}-{mode}-tb'
            if fw in cells and tb in cells: comparisons.append(([fw,tb],(('policy','algorithm'),),'FW-TB'))
        for algorithm in ('fw','tb'):
            modes=[f'{profile}-{mode}-{algorithm}' for mode in ('local','redis')]
            if all(cell in cells for cell in modes): comparisons.append((modes,(('policy','mode'),),'local-redis'))
        baseline=[f'{profile}-none',f'{profile}-local-fw',f'{profile}-redis-fw']
        if all(cell in cells for cell in baseline): comparisons.append((baseline,(('policy','mode'),),'no-local-redis'))
    for group, ignored, label in comparisons:
        group=[cell for cell in group if cell in cells]
        if len({json.dumps(signature(cell, ignored), sort_keys=True) for cell in group}) != 1:
            raise ValueError('uncontrolled contrast '+label+': '+','.join(group))
        by_run={cell:{entry['repetition']:entry for entry in entries if entry['cell']==cell} for cell in group}
        for rep in ('1','2','3'):
            fingerprints={by_run[cell][rep]['image_fingerprint'] for cell in group}
            if len(fingerprints)!=1:
                raise ValueError('image content mismatch across controlled contrast: '+','.join(group))
    for mode in ('none','local','redis'):
        for rate in (50,180,250):
            group=[f'scale-{mode}-fw-{n}api-{rate}rps' for n in (1,2,4)]
            if len({json.dumps(signature(cell, (('topology','api_instances'),)), sort_keys=True) for cell in group}) != 1:
                raise ValueError('uncontrolled scaling contrast: '+mode+' '+str(rate))
    for group in (['outage-open-healthy','outage-open-outage'], ['outage-closed-healthy','outage-closed-outage']):
        normalized={}
        for cell in group:
            item=json.loads(json.dumps(cells[cell]))
            workload=dict(item['workload']); workload.pop('pause_at_s',None); workload.pop('pause_for_s',None)
            item['workload']=workload
            item.pop('id',None)
            normalized[cell]=item
        if len({json.dumps(normalized[cell], sort_keys=True) for cell in group}) != 1:
            raise ValueError('outage pair mismatch: '+','.join(group))
        paired={cell:{entry['repetition']:entry for entry in entries if entry['cell']==cell} for cell in group}
        if any(paired[group[0]][rep]['image_fingerprint']!=paired[group[1]][rep]['image_fingerprint'] for rep in ('1','2','3')):
            raise ValueError('outage pair image content mismatch: '+','.join(group))
    return manifest, rows, by_cell


def number(row, key):
    value = row.get(key, '')
    if value in ('', None):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def assert_export_value(row, key, expected, run_id):
    observed=number(row,key)
    if expected is None and observed is None: return
    if expected is None or observed is None or not math.isclose(float(expected),observed,rel_tol=1e-12,abs_tol=1e-9):
        raise ValueError(f'export/raw mismatch {run_id} {key}: {observed} != {expected}')


def stats(selected, metric):
    values = [number(row, metric) for row in selected]
    values = [value for value in values if value is not None]
    if len(values) != len(selected) or not values:
        return None
    return median(values), min(values), max(values)


def aggregate(by_cell):
    result=[]
    for cell, selected in by_cell.items():
        for metric in METRICS:
            values=stats(selected,metric)
            if values:
                result.append(dict(cell=cell,metric=metric,median=values[0],minimum=values[1],maximum=values[2]))
    return result


def load_json(path):
    return json.loads(Path(path).read_text())


def check_hash(path, expected, label):
    if not expected or sha(path) != expected:
        raise ValueError('archive artifact checksum mismatch: '+label)


def locate_case(entry, roots):
    expected=entry['raw_checksums'].get('analysis.json')
    planned=entry['planned_run_id']
    source_path=entry['path']
    source='v1.1'
    if '/artifacts/protocol-v1.2/' in source_path: source='v1.2'
    elif '/artifacts/protocol-v1.3/' in source_path: source='v1.3'
    root=roots[source]
    direct=None
    if source=='v1.1':
        suffix=source_path.split('/artifacts/protocol-v1.1/',1)[1]
        direct=root/'raw/artifacts/protocol-v1.1'/suffix
    elif source=='v1.2':
        suffix=source_path.split('/artifacts/protocol-v1.2/',1)[1]
        direct=root/'source-raw/artifacts-protocol-v1.2'/suffix
    else:
        direct=root/'attempt/raw'
    if direct is None or not (direct/'analysis.json').is_file():
        raise ValueError(f'accepted raw analysis path missing for {planned}: {direct}')
    if sha(direct/'analysis.json')!=expected:
        raise ValueError(f'accepted raw analysis path/hash mismatch for {planned}: {direct}')
    return source,direct


def parse_network_interval(log_path):
    pattern=re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z)$')
    times=[]
    with Path(log_path).open() as stream:
        for line in stream:
            match=pattern.match(line.strip())
            if match: times.append(datetime.fromisoformat(match.group(1).replace('Z','+00:00')).timestamp())
    if len(times)<2:
        return None, len(times)
    return times[-1]-times[0], len(times)


def enrich_runs(rows, result_manifest, locked_manifest, roots, exporter_path):
    entries={(entry['cell'],str(entry['repetition'])):entry for entry in result_manifest['runs']}
    spec=importlib.util.spec_from_file_location('pinned_report_study',exporter_path)
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    enriched=[]
    for row in rows:
        entry=entries[(row['cell'],row['repetition'])]
        source,case=locate_case(entry,roots)
        checksums=entry['raw_checksums']
        for name in ('analysis.json','load/summary.json','load/metadata.json','redis-resources.log','images.json','image-inspect.json'):
            expected=checksums.get(name)
            path=case/name
            if expected:
                check_hash(path,expected,f"{entry['planned_run_id']}:{name}")
            elif name!='redis-resources.log':
                raise ValueError(f"manifest missing required checksum {name}: {entry['planned_run_id']}")
        redis_declared=checksums.get('redis-resources.log') is not None
        analysis=load_json(case/'analysis.json')
        metadata=load_json(case/'load/metadata.json')
        if metadata.get('git_revision')!=SOURCE_REVISION or analysis.get('run_id')!=row['run_id']:
            raise ValueError('accepted source/run ID mismatch: '+entry['planned_run_id'])
        deltas=analysis.get('counter_deltas',{})
        api=[value for key,value in deltas.items() if key.startswith('api')]
        images=load_json(case/'images.json');inspect=load_json(case/'image-inspect.json');image_flags=[];image_services={}
        if not isinstance(images,list) or not isinstance(inspect,list): raise ValueError('image identity input malformed: '+entry['planned_run_id'])
        for image in images:
            parts=image.get('ContainerName','').rsplit('-',2)
            if len(parts)!=3: raise ValueError('image container name malformed: '+entry['planned_run_id'])
            image_services[parts[1]]=exporter.image_identity(image,inspect,image_flags)
        if image_flags: raise ValueError('archived image identity invalid: '+entry['planned_run_id']+' '+','.join(image_flags))
        backend=deltas.get('backend',{})
        oracle=analysis.get('oracle',{})
        envelope=oracle.get('observed_global_accepted_envelope',[])
        bounds=[x.get('shared_quota_overshoot_lower_bound',x.get('above_single_shared_bucket_lower_bound')) for x in envelope]
        redis=analysis.get('redis_resources') or {}
        if redis.get('status')=='observed' and not redis_declared:
            raise ValueError('observed Redis resources lack archived sampler log: '+entry['planned_run_id'])
        interval=None; sample_count=None
        if checksums.get('redis-resources.log'):
            interval,sample_count=parse_network_interval(case/'redis-resources.log')
            if sample_count!=redis.get('samples') or interval is None:
                raise ValueError('network sampler timestamps/count mismatch: '+entry['planned_run_id'])
            for direction in ('input','output'):
                delta=redis.get(f'network_{direction}_bytes_delta')
                recorded=redis.get(f'network_{direction}_bytes_per_second')
                if delta is not None and recorded is not None and not math.isclose(float(delta)/interval,float(recorded),rel_tol=.005):
                    raise ValueError('network rate does not match INFO sample interval: '+entry['planned_run_id'])
        outage=analysis.get('outage') or {}; phases=outage.get('phases',{}); recovery=outage.get('recovery',{})
        api_allowed=sum(x.get('allowed',0) for x in api) if api else None
        api_rejected=sum(x.get('rejected',0) for x in api) if api else None
        record=dict(row)
        record.pop('path',None)
        record.update(planned_run_id=entry['planned_run_id'],accepted_artifact_source=source,
                      accepted_artifact_relative_path=str(case.relative_to(roots[source])),
                      raw_analysis_sha256=checksums['analysis.json'],raw_summary_sha256=checksums['load/summary.json'],
                      raw_network_log_sha256=checksums.get('redis-resources.log'),
                      raw_images_sha256=checksums['images.json'],raw_image_inspect_sha256=checksums['image-inspect.json'],
                      source_revision=metadata.get('git_revision'),oracle_status=oracle.get('status'),
                      runtime_identity=json.dumps({k:metadata.get(k) for k in ('workload_version','go_version','os','arch','cpu_count','gomaxprocs','hostname')},sort_keys=True,separators=(',',':')),
                      image_services_identity=json.dumps(image_services,sort_keys=True,separators=(',',':')),
                      oracle_violations=len(oracle.get('violations',[])),
                      oracle_overshoot_lower_bound=max((x for x in bounds if isinstance(x,(int,float))),default=None),
                      api_allowed=api_allowed,api_rejected=api_rejected,
                      backend_success=backend.get('success'),backend_canceled=backend.get('canceled'),
                      redis_average_cpu_cores=redis.get('average_cpu_cores'),
                      redis_memory_bytes_first=redis.get('memory_bytes_first'),redis_memory_bytes_last=redis.get('memory_bytes_last'),
                      redis_network_input_bytes_delta=redis.get('network_input_bytes_delta'),
                      redis_network_input_bytes_per_second=(redis.get('network_input_bytes_delta')/interval if interval and redis.get('network_input_bytes_delta') is not None else None),
                      redis_network_output_bytes_delta=redis.get('network_output_bytes_delta'),
                      redis_network_output_bytes_per_second=(redis.get('network_output_bytes_delta')/interval if interval and redis.get('network_output_bytes_delta') is not None else None),
                      redis_network_sample_interval_s=interval,redis_network_sample_count=sample_count,
                      redis_resource_status=redis.get('status','not_sampled'),
                      outage_stable_recovery_ms=recovery.get('stable_recovery_ms'),
                      outage_first_success_ms=recovery.get('first_legitimate_success_after_unpause_ms'))
        for key, phase in (('before','before'),('pausing','pausing'),('paused','outage'),('unpausing','unpausing'),('after','after')):
            record['outage_'+key+'_availability']=phases.get(phase,{}).get('legitimate_availability')
        summary=load_json(case/'load/summary.json')
        record['http_timeouts']=summary.get('timeouts')
        record['legitimate_sent']=summary.get('legitimate_sent')
        record['legitimate_successful']=summary.get('legitimate_successful')
        record['measurement_duration_s']=summary.get('elapsed_seconds_including_drain')
        if not record['measurement_duration_s'] or not math.isclose(
                float(summary.get('legitimate_goodput_per_second', math.nan)),
                float(summary.get('legitimate_successful', math.nan))/float(record['measurement_duration_s']),
                rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError('goodput numerator/duration mismatch: '+entry['planned_run_id'])
        if entry['cell'].endswith('-healthy'):
            sent=summary.get('legitimate_sent',0); successful=summary.get('legitimate_successful',0)
            record['healthy_legitimate_availability']=successful/sent if sent else None
        else:
            record['healthy_legitimate_availability']=None
        phases_dist=analysis.get('phase_distributions',{}).get('burst',{})
        for phase_name,phase_key in (('burst_base','base'),('burst_peak','burst')):
            distribution=phases_dist.get(phase_key,{}).get('legitimate/success',{}).get('latency_ms',{})
            for percentile in ('p50','p95','p99'):
                record[f'{phase_name}_{percentile}_ms']=distribution.get(percentile)
        if row['oracle_status']!=record['oracle_status']:
            raise ValueError('CSV and pinned raw oracle status disagree: '+entry['planned_run_id'])
        for export_key, raw_value in (('backend_arrivals',backend.get('arrivals')),('backend_overload',backend.get('overload')),
                                      ('http_2xx',summary.get('http_2xx')),('http_429',summary.get('http_429')),
                                      ('http_5xx',summary.get('http_5xx')),('timeouts',summary.get('timeouts')),
                                      ('observed_oracle_violations',len(oracle.get('violations',[]))),
                                      ('max_global_envelope_overshoot_lower_bound',record['oracle_overshoot_lower_bound']),
                                      ('redis_average_cpu_cores',redis.get('average_cpu_cores')),
                                      ('redis_memory_bytes_first',redis.get('memory_bytes_first')),
                                      ('redis_memory_bytes_last',redis.get('memory_bytes_last'))):
            assert_export_value(row,export_key,raw_value,entry['planned_run_id'])
        latency=analysis.get('distributions',{}).get('legitimate/success',{}).get('latency_ms',{})
        for percentile in ('p50','p95','p99'):
            assert_export_value(row,'legitimate_'+percentile+'_ms',latency.get(percentile),entry['planned_run_id'])
        api_errors=sum(x.get('limiter_errors',0) for x in api) if api else None
        assert_export_value(row,'limiter_errors',api_errors,entry['planned_run_id'])
        for phase,source_phase in (('before','before'),('pausing','pausing'),('outage','paused'),('unpausing','unpausing'),('after','after')):
            assert_export_value(row,'outage_'+phase+'_legitimate_availability',phases.get(source_phase if source_phase!='paused' else 'outage',{}).get('legitimate_availability'),entry['planned_run_id'])
        assert_export_value(row,'stable_recovery_ms',recovery.get('stable_recovery_ms'),entry['planned_run_id'])
        if any(v is None for v in (record['api_allowed'],record['api_rejected'])):
            raise ValueError('API allow/reject counters missing: '+entry['planned_run_id'])
        enriched.append(record)
    return enriched


def verify_archived_runtime_and_images(records, manifest):
    runtime={r['runtime_identity'] for r in records}
    if len(runtime)!=1 or 'null' in next(iter(runtime)):
        raise ValueError('runtime differs or is incomplete across selected runs')
    service_identities={}
    for row in records:
        for service,identity in json.loads(row['image_services_identity']).items():
            service_identities.setdefault(service,set()).add(json.dumps(identity,sort_keys=True))
    if any(len(values)!=1 for values in service_identities.values()):
        changed={k:len(v) for k,v in service_identities.items() if len(v)!=1}
        raise ValueError('shared service image contents differ across measured cells: '+json.dumps(changed,sort_keys=True))
    contrast=[]
    cells={c['id']:c for c in manifest['cells']}
    for profile in ('normal','mixed','burst'):
        for mode in ('local','redis'):
            contrast.append(dict(rq='RQ1/RQ2',profile=profile,mode=mode,factor='policy.algorithm',levels=['fixed-window','token-bucket']))
        contrast.append(dict(rq='RQ1/RQ2/RQ5',profile=profile,factor='policy.mode',levels=['none','local','redis']))
    for mode in ('none','local','redis'):
        for rate in (50,180,250): contrast.append(dict(rq='RQ3',mode=mode,rps=rate,factor='topology.api_instances',levels=[1,2,4]))
        for api in (1,2,4): contrast.append(dict(rq='RQ3',mode=mode,api_instances=api,factor='workload.rps',levels=[50,180,250]))
    contrast += [dict(rq='RQ5',policy=p,factor='workload.pause_at_s/pause_for_s',levels=['healthy','outage']) for p in ('open','closed')]
    return dict(runtime_signatures=len(runtime),shared_service_image_signatures={k:1 for k in sorted(service_identities)},
                same_revision=all(r['source_revision']==SOURCE_REVISION for r in records),contrasts=contrast)


def check_archives(args):
    for name,path in (('v12_archive',args.v12_archive),('v13_archive',args.v13_archive)):
        check_hash(path,PINS[name],name)
    v11_archive=args.v12_package/'source-raw/previous-v1.1-resume-evidence.tar.gz'
    check_hash(v11_archive,PINS['v11_archive'],'nested v1.1 archive')
    check_hash(args.v11_root/'SHA256SUMS',PINS['v11_bundle_sums'],'v1.1 file checksum index')
    check_hash(args.v12_package/'SHA256SUMS',PINS['v12_bundle_sums'],'v1.2 file checksum index')
    check_hash(args.v13_package/'SHA256SUMS',PINS['v13_bundle_sums'],'v1.3 file checksum index')
    check_hash(args.v11_root/'raw/coordinator/formal-results/attempts.jsonl',PINS['v11_ledger'],'v1.1 ledger')
    check_hash(args.v12_package/'results/coordinator-output/attempts.jsonl',PINS['v12_ledger'],'v1.2 ledger')
    check_hash(args.v12_package/'retry-summary.json','3416aa13af0f78b5af73f1fc60158b377d821e78199dd25e6009a80482c0a16d','v1.2 retry summary')
    check_hash(args.v13_package/'provenance/export/scripts/report-study.py',PINS['exporter'],'pinned exporter')
    check_hash(args.v13_package/'attempt/receipts/attempt.json','da219c555190e880f4620f6acf28fb8c48ae492a53706a883fae456dd1faee51','v1.3 attempt receipt')
    result_manifest=args.v13_package/'final-export/export/manifest.json'
    runs_path=args.v13_package/'final-export/export/runs.csv'
    roots={'v1.1':args.v11_root,'v1.2':args.v12_package,'v1.3':args.v13_package}
    return result_manifest,runs_path,roots


def read_ledger(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def ledger_archive_path(source, run_path, args):
    if not run_path:
        return None
    if source=='v1.1':
        marker='/artifacts/protocol-v1.1/'
        if marker not in run_path: return None
        base=args.v11_root/'raw/artifacts/protocol-v1.1'; suffix=run_path.split(marker,1)[1]
        candidate=base/suffix
        if candidate.exists(): return 'v1.1/'+str(candidate.relative_to(args.v11_root))
    else:
        marker='/artifacts/protocol-v1.2/'
        if marker not in run_path: return None
        base=args.v12_package/'source-raw/artifacts-protocol-v1.2'; suffix=run_path.split(marker,1)[1]
        candidate=base/suffix
        if candidate.exists(): return 'v1.2/'+str(candidate.relative_to(args.v12_package))
    return None


def retry_history(args):
    old=read_ledger(args.v11_root/'raw/coordinator/formal-results/attempts.jsonl')
    new=read_ledger(args.v12_package/'results/coordinator-output/attempts.jsonl')
    imported=load_json(args.v12_package/'results/coordinator-output/imported-results.json')
    import_state=load_json(args.v12_package/'results/coordinator-output/import-state.json')
    if sha(args.v12_package/'results/coordinator-output/imported-results.json')!=import_state.get('imported_results_sha256'):
        raise ValueError('corrected v1.1 import selection checksum mismatch')
    if sha(args.v12_package/'results/coordinator-output/import-attempts.jsonl')!=import_state.get('import_ledger_sha256') or import_state.get('source_ledger_sha256')!=PINS['v11_ledger']:
        raise ValueError('corrected v1.1 import ledger provenance mismatch')
    old_end=[x for x in old if x.get('event')=='attempt_finished']
    new_end=[x for x in new if x.get('event')=='attempt_finished']
    def rejected_reasons(event):
        return sorted({reason for check in event.get('checks',{}).values() for reason in check.get('reasons',[])})
    selected=[]; invalid=[]
    for source, events in (('v1.1',old_end),('v1.2',new_end)):
        for event in events:
            reasons=rejected_reasons(event)
            if event.get('accepted') is False:
                invalid.append(dict(source=source,planned_id=event.get('invocation_id'),attempt=event.get('attempt'),reasons=reasons,
                                    archive_relative_path=ledger_archive_path(source,event.get('run_path'),args)))
            if event.get('invocation_id') in ('p1-128-scale-none-fw-4api-250rps-r3','p1-129-scale-redis-fw-1api-250rps-r3'):
                selected.append(dict(source=source,planned_id=event.get('invocation_id'),attempt=event.get('attempt'),accepted=event.get('accepted'),reasons=reasons,
                                     archive_relative_path=ledger_archive_path(source,event.get('run_path'),args)))
    receipt=load_json(args.v13_package/'attempt/receipts/attempt.json')
    if receipt.get('planned_run_id')!='p1-129-scale-redis-fw-1api-250rps-r3' or receipt.get('source_revision')!=SOURCE_REVISION or receipt.get('runner_exit_code')!=0:
        raise ValueError('v1.3 retry receipt does not match the authorized passing attempt')
    selected.append(dict(source='v1.3',planned_id=receipt['planned_run_id'],attempt=1,accepted=True,reasons=[],
                         archive_relative_path='v1.3/attempt/raw'))
    return dict(
        v1_1=dict(started=sum(x.get('event')=='attempt_started' for x in old),finished=len(old_end),accepted=sum(x.get('accepted') is True for x in old_end),rejected=sum(x.get('accepted') is False for x in old_end),unfinished=sum(x.get('event')=='attempt_started' for x in old)-len(old_end),initial_rejection_reasons=dict(__import__('collections').Counter(r for x in old_end for r in rejected_reasons(x))),corrected_import_accepted=len(imported['runs']),corrected_import_missing=len(imported['missing_planned_run_ids']),imported_results_sha256=import_state['imported_results_sha256']),
        v1_2=dict(started=sum(x.get('event')=='attempt_started' for x in new),finished=len(new_end),accepted=sum(x.get('accepted') is True for x in new_end),rejected=sum(x.get('accepted') is False for x in new_end),rejection_reasons=dict(__import__('collections').Counter(r for x in new_end for r in rejected_reasons(x)))),
        v1_3=dict(planned_id=receipt['planned_run_id'],attempts=1,accepted=True,reason='frozen checker passed',receipt_sha256=sha(args.v13_package/'attempt/receipts/attempt.json')),
        focused_attempts=selected,
        invalid_attempts=invalid,
        ledger_sha256={'v1.1':PINS['v11_ledger'],'v1.2':PINS['v12_ledger']},
        selection_rule='Earliest complete qualifying attempt per planned run ID; selection is based on validation, never performance.',
        final_selected_count=138)


def write_csv(path, rows):
    fields=list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def display_cell(by_cell,cell,metric):
    values=stats(by_cell[cell],metric)
    return '—' if values is None else f'{values[0]:.3f} ({values[1]:.3f}–{values[2]:.3f})'


def profile_cell_ids(profile, mode):
    return [f'{profile}-none'] if mode=='none' else [f'{profile}-{mode}-{algo}' for algo in ('fw','tb')]


def rq1_cell_row(by_cell, cell):
    if cell.endswith('-none'):
        values=' | '.join(display_cell(by_cell,cell,k) for k in ('legitimate_goodput_per_second','legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))+' | — | —'
        return '| '+cell+' | '+values+' | không áp dụng | — | — |'
    statuses=','.join(sorted({r['oracle_status'] for r in by_cell[cell]}))
    values=' | '.join(display_cell(by_cell,cell,k) for k in ('legitimate_goodput_per_second','legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms','api_allowed','api_rejected'))
    return '| '+cell+' | '+values+f' | {statuses} | {display_cell(by_cell,cell,"oracle_violations")} | {display_cell(by_cell,cell,"oracle_overshoot_lower_bound")} |'


def make_summary_tables(by_cell, retries, manifest, output):
    lines=['# Bảng kết quả sinh từ tệp xuất và artifact đã xác minh','',
           'Các số liên tục hiển thị median (min–max) của ba lượt. Goodput từng lượt = legitimate_successful / elapsed_seconds_including_drain; hai toán hạng được giữ trong `run-evidence.csv`. p50/p95/p99 là percentile từng lượt rồi tổng hợp; không gộp trace. Ô trống nghĩa là không đo hoặc không áp dụng.','',
           '## RQ1 — thuật toán, chế độ và workload','',
           '| Ô | Goodput khách hợp lệ/s | p50 ms | p95 ms | p99 ms | Cho phép | Từ chối | Oracle | Số vi phạm | Cận dưới overshoot |','|---|---:|---:|---:|---:|---:|---:|---|---:|---:|']
    for profile in ('normal','mixed','burst'):
        for mode in ('none','local','redis'):
            for cell in profile_cell_ids(profile,mode):
                if cell in by_cell: lines.append(rq1_cell_row(by_cell,cell))
    lines += ['', 'Các percentile p50/p95/p99 trong hai pha burst (phản hồi hợp lệ thành công) được giữ theo từng lượt trong `run-evidence.csv`, gồm pha nền và pha đỉnh. Ô trống nghĩa là lượt đó không có metric/pha tương ứng.','',
              '## RQ2 — local và Redis: chi phí, correctness, tài nguyên','',
              '| Workload | Thuật toán | Goodput/s local→Redis | p50/p95/p99 ms local→Redis | API cho phép/từ chối local→Redis | Oracle local→Redis | CPU Redis (core) | Bộ nhớ Redis đầu→cuối (byte) | Network vào delta/tốc độ | Network ra delta/tốc độ | Khoảng mẫu/số mẫu |','|---|---|---:|---|---|---|---:|---|---|---|---|']
    for profile in ('normal','mixed','burst'):
        for algo in ('fw','tb'):
            local=f'{profile}-local-{algo}'; redis=f'{profile}-redis-{algo}'
            if local not in by_cell or redis not in by_cell: continue
            percentiles='/'.join(display_cell(by_cell,local,k) for k in ('legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))+' → '+'/'.join(display_cell(by_cell,redis,k) for k in ('legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))
            resource=f"{display_cell(by_cell,redis,'redis_average_cpu_cores')} | {display_cell(by_cell,redis,'redis_memory_bytes_first')}→{display_cell(by_cell,redis,'redis_memory_bytes_last')}"
            netin=f"{display_cell(by_cell,redis,'redis_network_input_bytes_delta')} B / {display_cell(by_cell,redis,'redis_network_input_bytes_per_second')} B/s"
            netout=f"{display_cell(by_cell,redis,'redis_network_output_bytes_delta')} B / {display_cell(by_cell,redis,'redis_network_output_bytes_per_second')} B/s"
            interval=f"{display_cell(by_cell,redis,'redis_network_sample_interval_s')} s / {display_cell(by_cell,redis,'redis_network_sample_count')}"
            local_c=' / '.join(display_cell(by_cell,local,k) for k in ('api_allowed','api_rejected'))
            redis_c=' / '.join(display_cell(by_cell,redis,k) for k in ('api_allowed','api_rejected'))
            statuses=','.join(sorted({r['oracle_status'] for r in by_cell[local]}))+' → '+','.join(sorted({r['oracle_status'] for r in by_cell[redis]}))
            lines.append(f'| {profile} | {algo.upper()} | {display_cell(by_cell,local,"legitimate_goodput_per_second")} → {display_cell(by_cell,redis,"legitimate_goodput_per_second")} | {percentiles} | {local_c} → {redis_c} | {statuses} | {resource} | {netin} | {netout} | {interval} |')
    lines += ['', 'Trường tài nguyên Redis để trống ở ô không có bộ lấy mẫu; trống không có nghĩa là zero. Network là tổng bộ đếm TCP của Redis, gồm workload, sampler, healthcheck và thao tác admin; khoảng mẫu tính từ ảnh chụp INFO hợp lệ đầu tiên tới cuối cùng. Pha outage không có mẫu tài nguyên/network.','',
              '## RQ3 — 50/180/250 RPS × 1/2/4 API','',
              '| Chế độ | RPS | Số API | Goodput/s | p50/p95/p99 ms | Backend đến/thành công/quá tải/hủy |','|---|---:|---:|---:|---|---|']
    for mode in ('none','local','redis'):
        for rate in (50,180,250):
            for api in (1,2,4):
                cell=f'scale-{mode}-fw-{api}api-{rate}rps'
                back='/'.join(display_cell(by_cell,cell,k) for k in ('backend_arrivals','backend_success','backend_overload','backend_canceled'))
                tails='/'.join(display_cell(by_cell,cell,k) for k in ('legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))
                lines.append(f'| {mode} | {rate} | {api} | {display_cell(by_cell,cell,"legitimate_goodput_per_second")} | {tails} | {back} |')
    lines += ['', '## RQ5 — bảo vệ backend và outage','',
              '| Profile/chế độ/thuật toán | Goodput khách hợp lệ/s | p50/p95/p99 ms | Backend đến/thành công/quá tải/hủy | 429/timeouts/5xx |','|---|---:|---|---|---|']
    for profile in ('mixed','burst'):
        for mode in ('none','local','redis'):
            for cell in profile_cell_ids(profile,mode):
                if cell not in by_cell: continue
                b='/'.join(display_cell(by_cell,cell,k) for k in ('backend_arrivals','backend_success','backend_overload','backend_canceled'))
                tails='/'.join(display_cell(by_cell,cell,k) for k in ('legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))
                http='/'.join(display_cell(by_cell,cell,k) for k in ('http_429','http_timeouts','http_5xx'))
                lines.append(f'| {cell} | {display_cell(by_cell,cell,"legitimate_goodput_per_second")} | {tails} | {b} | {http} |')
    lines += ['', '### Hồi phục sau outage','',
              '| Policy | Pha đo | Khả dụng baseline khỏe | Trước/yêu cầu pause/pause/unpause/sau — khả dụng | Goodput/s | p50/p95/p99 ms | Backend đến/thành công/quá tải/hủy | 429/timeouts/5xx | Hồi phục ổn định ms | Thành công đầu tiên sau unpause ms |','|---|---|---:|---|---:|---|---|---|---:|---:|']
    for policy in ('open','closed'):
        for phase in ('healthy','outage'):
            cell=f'outage-{policy}-{phase}'
            avail='/'.join(display_cell(by_cell,cell,'outage_'+x+'_availability') for x in ('before','pausing','paused','unpausing','after'))
            back='/'.join(display_cell(by_cell,cell,k) for k in ('backend_arrivals','backend_success','backend_overload','backend_canceled'))
            tails='/'.join(display_cell(by_cell,cell,k) for k in ('legitimate_p50_ms','legitimate_p95_ms','legitimate_p99_ms'))
            http='/'.join(display_cell(by_cell,cell,k) for k in ('http_429','http_timeouts','http_5xx'))
            lines.append(f'| {policy} | {phase} | {display_cell(by_cell,cell,"healthy_legitimate_availability")} | {avail} | {display_cell(by_cell,cell,"legitimate_goodput_per_second")} | {tails} | {back} | {http} | {display_cell(by_cell,cell,"outage_stable_recovery_ms")} | {display_cell(by_cell,cell,"outage_first_success_ms")} |')
    recovery=manifest['recovery']; thresholds=recovery['frozen_p95_threshold_ms']
    lines += ['', f"Quy tắc hồi phục ổn định dùng cửa sổ khóa {recovery['window_ms']} ms, ít nhất {recovery['min_legitimate_samples']} mẫu hợp lệ và {recovery['consecutive_clean_windows']} cửa sổ sạch liên tiếp; ngưỡng p95 healthy cố định là fail-open {thresholds['open']} ms và fail-closed {thresholds['closed']} ms. Lần thành công đầu tiên được báo riêng, không đồng nhất với hồi phục ổn định.",'',
              '### Lịch sử retry/lượt không hợp lệ','',
              '| Giai đoạn | Bắt đầu/hoàn tất | Được nhận | Không hợp lệ/bị loại | Lý do loại chính |','|---|---:|---:|---:|---|']
    for label,key in (('v1.1 original ledger','v1_1'),('v1.2 continuation ledger','v1_2')):
        x=retries[key]; reasons=', '.join(f'{k}={v}' for k,v in x.get('rejection_reasons',x.get('initial_rejection_reasons',{})).items()) or 'none'
        lines.append(f"| {label} | {x['started']}/{x['finished']} | {x['accepted']} | {x['rejected']} (unfinished {x.get('unfinished',0)}) | {reasons} |")
    lines += ['', 'Import offline v1.1 sau khi sửa checker chọn 104 lượt hợp lệ và còn thiếu 34 lượt sau khi thẩm định lại; ledger ban đầu ghi sáu lần loại `same_cell_fingerprint_mismatch` do nhãn Compose project riêng từng attempt. V1.2 hoàn tất 36 attempt mới: nhận 31, loại 5 vì `generator_drops`. Manifest kết quả chọn attempt đủ điều kiện sớm nhất, không chọn theo hiệu năng. Cụ thể p1-128 trượt attempt 1–2 vì `generator_drops`, attempt 3 đạt; p1-129 trượt attempt v1.2 1–3 vì `generator_drops`, sau đó attempt v1.3 duy nhất được cho phép đã đạt. `retry-history.json` lưu lý do và đường dẫn tương đối trong archive của từng attempt; không xóa attempt lỗi.','']
    Path(output/'T10_TABLES.md').write_text('\n'.join(lines))


def create_output(path):
    Path(path).mkdir(parents=True,exist_ok=False)


def make_figures(by_cell, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=False)
    def save(name, title, groups, metric, ylabel, labels=None, xticklabels=None):
        labels=labels or groups
        colors=['#126782','#d07a16','#398552','#9b4f96']
        markers=['o','s','^','D']
        fig,ax=plt.subplots(figsize=(9,5))
        for gi,(label,cells) in enumerate(zip(labels,groups)):
            xs=[]; ys=[]; lows=[]; highs=[]
            for i,cell in enumerate(cells):
                value=stats(by_cell[cell],metric)
                if not value: continue
                xs.append(i+1); ys.append(value[0]); lows.append(value[0]-value[1]); highs.append(value[2]-value[0])
            if xs: ax.errorbar(xs,ys,yerr=[lows,highs],marker=markers[gi%len(markers)],capsize=3,color=colors[gi%len(colors)],label=label)
        ax.set_xticks(range(1,len(groups[0])+1),xticklabels or [str(i) for i in range(1,len(groups[0])+1)])
        ax.set_xlabel('Cấu hình protocol')
        ax.set_ylabel(ylabel); ax.set_title(title); ax.grid(axis='y',alpha=.25); ax.legend()
        fig.tight_layout(rect=(0,.13,1,1))
        fig.text(.5,.035,'Điểm: median của 3 lượt; thanh sai số: min–max.',ha='center',fontsize=8)
        for extension in ('svg','pdf','png'):
            fig.savefig(output/(name+'.'+extension),bbox_inches='tight',pad_inches=.12,dpi=160 if extension=='png' else None)
        plt.close(fig)
    def save_outage():
        vals=[]
        for label,cell in (('Fail-open','outage-open-outage'),('Fail-closed','outage-closed-outage')):
            avail=[number(row,'outage_paused_availability') for row in by_cell[cell]]
            vals.append((label,[v for v in avail if v is not None]))
        fig,ax=plt.subplots(figsize=(9,5))
        for i,(label,values) in enumerate(vals):
            ax.scatter([i+1+j*.06 for j in range(len(values))],values,label=label)
        ax.set_xticks(range(1,3),[x[0] for x in vals])
        ax.set_ylim(-.05,1.05); ax.set_ylabel('Khả dụng khách hợp lệ trong pha Redis pause')
        ax.set_title('RQ5 — khả dụng trong pha Redis outage'); ax.grid(axis='y',alpha=.25)
        fig.tight_layout(rect=(0,.13,1,1))
        fig.text(.5,.035,'Mỗi điểm là một lượt trong pha pause; đủ 3 lượt mỗi policy.',ha='center',fontsize=8)
        for extension in ('svg','pdf','png'):
            fig.savefig(output/('rq5-outage.'+extension),bbox_inches='tight',pad_inches=.12,dpi=160 if extension=='png' else None)
        plt.close(fig)
    save('rq1-normal','RQ1 — goodput khách hợp lệ ở tải bình thường',
         [['normal-none','normal-local-fw','normal-redis-fw'],['normal-none','normal-local-tb','normal-redis-tb']],
         'legitimate_goodput_per_second','Goodput hợp lệ (request/s)',['FW','TB'],['No limiter','Local','Redis'])
    save('rq1-latency','RQ1 — p95 khách hợp lệ theo thuật toán/workload',
         [['normal-local-fw','mixed-local-fw','burst-local-fw'],['normal-redis-fw','mixed-redis-fw','burst-redis-fw'],
          ['normal-local-tb','mixed-local-tb','burst-local-tb'],['normal-redis-tb','mixed-redis-tb','burst-redis-tb']],
         'legitimate_p95_ms','Median p95 từng lượt (ms)',['Local FW','Redis FW','Local TB','Redis TB'],['Normal','Mixed','Burst'])
    save('rq5-mixed-backend','RQ5 — tải hỗn hợp: request backend quá tải',
         [['mixed-none','mixed-local-fw','mixed-redis-fw'],['mixed-none','mixed-local-tb','mixed-redis-tb']],
         'backend_overload','Số request backend quá tải',['FW','TB'],['No limiter','Local','Redis'])
    for mode in ('none','local','redis'):
        save('rq3-scale-'+mode,'RQ3 — khả năng mở rộng '+mode+' / Fixed Window',
             [[f'scale-{mode}-fw-{n}api-{rate}rps' for n in (1,2,4)] for rate in (50,180,250)],
             'legitimate_goodput_per_second','Goodput hợp lệ (request/s)',['50 RPS','180 RPS','250 RPS'],['1 API','2 API','4 API'])
    save('rq5-burst','RQ1/RQ2/RQ5 — tải burst: goodput hợp lệ',
         [['burst-none','burst-local-fw','burst-redis-fw'],['burst-none','burst-local-tb','burst-redis-tb']],
         'legitimate_goodput_per_second','Goodput hợp lệ (request/s)',['FW','TB'],['No limiter','Local','Redis'])
    save('rq2-redis-cpu','RQ2 — Redis CPU trong workload matched',
         [['normal-redis-fw','mixed-redis-fw','burst-redis-fw'],['normal-redis-tb','mixed-redis-tb','burst-redis-tb']],
         'redis_average_cpu_cores','Redis CPU trung bình (cores)',['Redis FW','Redis TB'],['Normal','Mixed','Burst'])
    save('rq2-redis-memory','RQ2 — Redis memory cuối run trong workload matched',
         [['normal-redis-fw','mixed-redis-fw','burst-redis-fw'],['normal-redis-tb','mixed-redis-tb','burst-redis-tb']],
         'redis_memory_bytes_last','Redis memory cuối run (bytes)',['Redis FW','Redis TB'],['Normal','Mixed','Burst'])
    save_outage()
    save('rq5-recovery','RQ5 — stable recovery theo cửa sổ protocol',
         [['outage-open-outage','outage-closed-outage']], 'outage_stable_recovery_ms',
         'Thời gian hồi phục ổn định (ms)',['Recovery'],['Fail-open','Fail-closed'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',default='docs/experiments/protocol-v1.2/manifest.json')
    parser.add_argument('--v12-archive',default='docs/worklog/2026-10-20-t09-v1.2/T09-V1.2-FORMAL-EVIDENCE.tar.gz')
    parser.add_argument('--v13-archive',default='docs/worklog/2026-10-20-t09-v1.3/T09-V1.3-MISSING-SLOT-EVIDENCE.tar.gz')
    parser.add_argument('--v11-root',required=True,help='extracted nested v1.1 evidence root')
    parser.add_argument('--v12-package',required=True,help='extracted v1.2 evidence package root')
    parser.add_argument('--v13-package',required=True,help='extracted v1.3 evidence package root')
    parser.add_argument('--output',required=True); args=parser.parse_args()
    args.v12_archive=Path(args.v12_archive);args.v13_archive=Path(args.v13_archive)
    args.v11_root=Path(args.v11_root);args.v12_package=Path(args.v12_package);args.v13_package=Path(args.v13_package)
    result_path,runs_path,roots=check_archives(args)
    manifest,rows,by_cell=load_export(runs_path,args.manifest,result_path)
    enriched=enrich_runs(rows,load_json(result_path),manifest,roots,args.v13_package/'provenance/export/scripts/report-study.py')
    audit=verify_archived_runtime_and_images(enriched,manifest)
    by_cell={cell:[r for r in enriched if r['cell']==cell] for cell in by_cell}
    history=retry_history(args)
    output=Path(args.output); create_output(output)
    write_csv(output/'run-evidence.csv',enriched)
    aggregates=aggregate(by_cell)
    write_csv(output/'summary.csv',aggregates)
    trace_keys=('planned_run_id','cell','repetition','accepted_artifact_source','accepted_artifact_relative_path','source_revision','raw_analysis_sha256','raw_summary_sha256','raw_network_log_sha256','raw_images_sha256','raw_image_inspect_sha256')
    write_csv(output/'traceability.csv',[{k:r.get(k) for k in trace_keys} for r in enriched])
    (output/'aggregates.json').write_text(json.dumps(aggregates,indent=2)+'\n')
    (output/'retry-history.json').write_text(json.dumps(history,indent=2)+'\n')
    (output/'contrast-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    make_summary_tables(by_cell,history,manifest,output)
    make_figures(by_cell,output/'figures')
    provenance=dict(protocol_id=manifest['protocol_id'],source_revision=manifest['source_revision'],exporter_revision='046654e27e08e2292d554fd96a594226ef86bc7e',validation_tool_revision='371ed1184800d81791821ab6b048243d6510fbcb',locked_manifest_sha256=sha(args.manifest),derived_manifest_sha256=sha(result_path),runs_csv_sha256=sha(runs_path),v12_archive_sha256=sha(args.v12_archive),v13_archive_sha256=sha(args.v13_archive),v11_archive_sha256=sha(args.v12_package/'source-raw/previous-v1.1-resume-evidence.tar.gz'),v11_ledger_sha256=sha(args.v11_root/'raw/coordinator/formal-results/attempts.jsonl'),v12_ledger_sha256=sha(args.v12_package/'results/coordinator-output/attempts.jsonl'),exporter_sha256=sha(args.v13_package/'provenance/export/scripts/report-study.py'),analysis_script_sha256=sha(__file__),run_count=len(enriched),usable_runs=sum(r['tooling_validity']=='usable' for r in enriched),cell_count=len(by_cell),accepted_sources={k:sum(r['accepted_artifact_source']==k for r in enriched) for k in roots})
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(provenance,sort_keys=True))


if __name__=='__main__': main()
