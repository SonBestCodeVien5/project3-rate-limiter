// Run with: node internal/console/index_test.js
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function resultUI(){
  const nodes=new Map();
  function element(){return {value:'',children:[],append(...children){this.children.push(...children);},replaceChildren(){this.children=[];},addEventListener(){}};}
  const context={document:{createElement:element,getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}},Intl};
  vm.createContext(context);
  const html=fs.readFileSync(__dirname+'/index.html','utf8');
  const helpers=html.slice(html.indexOf('const fmt ='),html.indexOf('function renderLive'));
  vm.runInContext("const $=id=>document.getElementById(id);let resultData=null;"+helpers,context);
  return {nodes,render(data){context.data=data;vm.runInContext('renderResult(data)',context);},select(value){nodes.get('resultRepeat').value=value;vm.runInContext('renderResult(resultData)',context);},text(){return nodes.get('kpis').children.map(c=>c.children[0].textContent);}};
}

test('selects repetitions, preserves selection and exposes incomplete evidence',()=>{
  const ui=resultUI(),data={run:{id:'one',request:{repetitions:3,custom:{instances:1,profile:'mixed'}}},summaries:{'1':{sent:11,legitimate_sent:1,legitimate_successful:0},'2':{sent:22,legitimate_sent:2,legitimate_successful:2,legitimate_success_latency:{p95_ms:9},generator_dropped:3}},analyses:{'2':{oracle:{status:'inconclusive'},counter_deltas:{api1:{limiter_errors:4}}}}};
  ui.render(data);assert.equal(ui.text()[0],'11');assert.equal(ui.text()[4],'Không có mẫu thành công');assert.match(ui.nodes.get('analysisStatus').textContent,/Chưa có analysis/);
  ui.select('2');assert.equal(ui.text()[0],'22');assert.equal(ui.text()[4],'9 ms');assert.equal(ui.text()[6],'3');assert.equal(ui.text()[7],'4');assert.match(ui.nodes.get('analysisStatus').textContent,/Chưa đủ bằng chứng/);
  ui.render(data);assert.equal(ui.text()[0],'22');
  ui.select('3');assert.equal(ui.text().length,0);assert.match(ui.nodes.get('resultNote').textContent,/Chưa có summary/);
});

test('concurrent does not display absent legitimate latency as zero milliseconds',()=>{
  const ui=resultUI();ui.render({run:{id:'batch',request:{repetitions:1,custom:{profile:'concurrent',instances:1}}},summaries:{'1':{legitimate_sent:0,legitimate_successful:0,legitimate_goodput_per_second:0,legitimate_success_latency:{p95_ms:0}}}});
  assert.equal(ui.text()[3],'Không áp dụng');assert.equal(ui.text()[4],'Không áp dụng');assert.equal(ui.text()[7],'Thiếu counters');
});

test('counts every API and refuses to report a total with missing counters',()=>{
  const ui=resultUI(),data={run:{id:'multi',request:{repetitions:1,custom:{instances:2}}},summaries:{'1':{sent:10}},analyses:{'1':{oracle:{status:'inconclusive_with_observed_violations'},counter_deltas:{api1:{limiter_errors:2},api2:{limiter_errors:3}}}}};
  ui.render(data);assert.equal(ui.text()[7],'5');assert.match(ui.nodes.get('analysisStatus').textContent,/có vi phạm quan sát được/);
  delete data.analyses['1'].counter_deltas.api2;
  ui.render(data);assert.equal(ui.text()[7],'Thiếu counters');assert.match(ui.nodes.get('resultNote').textContent,/limiter_errors before\/after/);
});

test('comparison refuses configuration differences and missing evidence',()=>{
  const html=fs.readFileSync(__dirname+'/index.html','utf8'),context={};vm.createContext(context);
  vm.runInContext(html.slice(html.indexOf('function stable('),html.indexOf('async function compareSaved')),context);
  const evidence=comparisonFixtures();
  context.evidence=evidence;assert.equal(vm.runInContext('comparisonProblems(evidence).length',context),0);
  delete evidence[0].policy.capacity;assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/thiếu policy capacity/);evidence[0].policy.capacity=20;
  evidence[0].summary.run_id='wrong';assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/run_id summary/);evidence[0].summary.run_id='custom-repeat-1';
  evidence[1].metadata.config.legitimate_clients=6;assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/workload/);
  evidence[1].metadata.config.legitimate_clients=5;evidence[2].images=[];assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/image identity/);
  evidence[0].gitStatus=' M internal/limiter/local.go';assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/working tree/);
  evidence[0].compose.services.api1.environment.MODE='redis';assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/Compose khác policy/);
});

function comparisonFixtures(){
  return ['none','local','redis'].map(mode=>({metadata:{config:{run_id:'custom-repeat-1',profile:'mixed',duration_ns:3,rps:120,legitimate_rps:20,legitimate_clients:5,max_inflight:200,timeout_ns:2,max_schedule_lag_ns:1,mode_label:mode},go_version:'go',os:'linux',arch:'amd64',cpu_count:12,gomaxprocs:12,hostname:'host',git_revision:'abc',git_status_porcelain:'',workload_version:2},revision:'abc',gitStatus:'',caseRepeat:'custom-repeat-1',summary:{run_id:'custom-repeat-1'},policy:{mode,algorithm:'fixed-window',fail_policy:'closed',state_reset:true,limit:20,window_ms:1000,capacity:20,rate_per_sec:20,namespace:mode},compose:{services:{api1:{environment:{MODE:mode,ALGORITHM:'fixed-window',NAMESPACE:mode}},backend:{environment:{BACKEND_CAPACITY:'4',BACKEND_SERVICE_TIME:'50ms'}},nginx:{},redis:{}}},images:['api1','backend','nginx','redis'].map(name=>({ContainerName:'lab-'+name+'-1',ID:name,Platform:'linux/amd64'})),baseImages:'digest',nginx:'upstream api1;'}));
}

test('matched artifact selections render individual results and quality evidence',async()=>{
  const evidence=comparisonFixtures(),nodes=new Map();
  function element(){return {value:'',children:[],style:{},append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}};}
  for(const [i,id] of ['compareNone','compareLocal','compareRedis'].entries()){nodes.set(id,element());nodes.get(id).value=JSON.stringify(['saved-'+i,'custom',1]);evidence[i].summary={run_id:'custom-repeat-1',legitimate_sent:10,legitimate_successful:10,legitimate_goodput_per_second:3,legitimate_success_latency:{p95_ms:12,p99_ms:15},http_429:2,http_5xx:1,timeouts:0,transport_errors:1,generator_dropped:0};evidence[i].analysis={oracle:{status:'inconclusive'},counter_deltas:{api1:{limiter_errors:2},backend:{arrivals:10,overload:1}}};}
  const context={Intl,document:{createElement:element,getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}},fetch:async url=>{
    const index=Number(url.match(/saved-(\d)/)[1]),e=evidence[index],name=url.split('/artifacts/')[1];
    const files={'load/metadata.json':e.metadata,'policy.json':e.policy,'compose-resolved.json':e.compose,'images.json':e.images,'base-image-digests.txt':e.baseImages,'git-revision.txt':e.revision,'git-status.txt':e.gitStatus,'load/summary.json':e.summary,'analysis.json':e.analysis,'topology/nginx.conf':e.nginx};const value=files[name.replace('custom-repeat-1/','')];return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value,text:async()=>value};
  }};
  vm.createContext(context);const html=fs.readFileSync(__dirname+'/index.html','utf8');
  vm.runInContext("const $=id=>document.getElementById(id);const fmt=v=>typeof v==='number'?String(v):'—';"+html.slice(html.indexOf('function stable('),html.indexOf("$('compare').addEventListener")),context);
  await vm.runInContext('compareSaved()',context);
  assert.match(nodes.get('compareStatus').textContent,/Cấu hình\/evidence khớp/);
  const rows=nodes.get('comparison').children[0].children.map(row=>row.children.map(cell=>cell.textContent));
  assert.equal(rows.find(row=>row[0]==='Run / lượt')[1],'saved-0 / custom-repeat-1');
  assert.equal(rows.find(row=>row[0]==='P99 hợp lệ thành công (ms)')[3],'15');
  assert.equal(rows.find(row=>row[0]==='Lỗi limiter · delta mọi API')[2],'2');
  assert.equal(rows.find(row=>row[0]==='Oracle · phạm vi trace')[1],'Chưa đủ bằng chứng');
  assert.equal(rows.find(row=>row[0]==='Lỗi truyền tải')[1],'1');
});


test('inspected image layers and full config identify matching content across IDs',()=>{
  const html=fs.readFileSync(__dirname+'/index.html','utf8'),context={};vm.createContext(context);
  vm.runInContext(html.slice(html.indexOf('function stable('),html.indexOf('async function compareSaved')),context);
  const evidence=comparisonFixtures();
  for(const [index,e] of evidence.entries()){
    e.images.forEach(image=>{image.ID+=String(index);});
    e.imageInspect=e.images.map(image=>({Id:image.ID,RootFS:{Type:'layers',Layers:['sha256:'+'a'.repeat(64)]},Config:{Env:['ROLE=app'],Entrypoint:['/app']},Os:'linux',Architecture:'amd64'}));
  }
  context.evidence=evidence;assert.equal(vm.runInContext('comparisonProblems(evidence).length',context),0);
  evidence[1].imageInspect[0].RootFS.Layers[0]='sha256:'+'b'.repeat(64);assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/images/);
  evidence[1].imageInspect[0].RootFS.Layers[0]='sha256:'+'a'.repeat(64);evidence[1].imageInspect[0].Config.Env=['ROLE=other'];assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/images/);
  evidence[1].imageInspect[0].Config.Env=['ROLE=app'];evidence[1].imageInspect[0].Id='forged';assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/không khớp ID/);
  evidence.forEach(e=>{delete e.imageInspect;});assert.match(vm.runInContext('comparisonProblems(evidence).join(";")',context),/images/);
});
