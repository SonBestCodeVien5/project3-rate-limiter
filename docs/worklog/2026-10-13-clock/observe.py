import json,time,pathlib
out=pathlib.Path('/tmp/project3-clock-observer')
samples=[]
start=time.monotonic_ns()
for _ in range(1801):
 m1=time.monotonic_ns();w=time.time_ns();m2=time.monotonic_ns()
 samples.append({'wall_ns':w,'monotonic_ns':(m1+m2)//2,'read_span_ns':m2-m1})
 if time.monotonic_ns()-start>=90_000_000_000:break
 time.sleep(.05)
steps=[]
for a,b in zip(samples,samples[1:]):
 wd=b['wall_ns']-a['wall_ns'];md=b['monotonic_ns']-a['monotonic_ns'];delta=wd-md
 if abs(delta)>5_000_000:steps.append({'wall_ns':b['wall_ns'],'wall_delta_ms':wd/1e6,'monotonic_delta_ms':md/1e6,'difference_ms':delta/1e6})
summary={'samples':len(samples),'elapsed_monotonic_seconds':(samples[-1]['monotonic_ns']-samples[0]['monotonic_ns'])/1e9,'elapsed_wall_seconds':(samples[-1]['wall_ns']-samples[0]['wall_ns'])/1e9,'clock_steps_above_5ms':steps,'max_read_span_us':max(s['read_span_ns'] for s in samples)/1e3,'clock_info':{k:vars(time.get_clock_info(k)) for k in ['time','monotonic']}}
(out/'samples.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
