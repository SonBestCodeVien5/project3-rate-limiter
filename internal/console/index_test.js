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
