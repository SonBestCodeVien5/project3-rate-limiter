const fs=require('fs');
const {execFileSync}=require('child_process');
const {chromium}=require('/home/khanhson2005/.npm/_npx/c44bce6a2a6e9da9/node_modules/playwright');
const out=process.cwd()+'/artifacts/monitoring/p2-03a-console';
const save=(n,x)=>fs.writeFileSync(out+'/'+n,JSON.stringify(x,null,2)+'\n');
async function get(url){const r=await fetch(url,{signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error('GET '+url+' '+r.status);return r.json()}
(async()=>{
 const before=await get('http://127.0.0.1:8090/api/runs');
 if(before.some(r=>r.started_at>='2026-10-24'))throw Error('Today run exists; refusing another attempt');
 const browser=await chromium.launch({headless:true,executablePath:'/home/khanhson2005/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome',args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1440,height:1100},storageState:'/tmp/p2-03a-browser-auth-private.json'});
 const page=await context.newPage();page.setDefaultTimeout(15000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let posts=0;
 await page.route('**/api/runs',async route=>{
  if(route.request().method()!=='POST')return route.continue();
  posts++;
  const r=route.request().postDataJSON(),c=r.custom;
  const good=posts===1&&r.case==='custom'&&r.monitoring===true&&r.repetitions===1&&c.profile==='normal'&&c.mode==='redis'&&c.algorithm==='fixed-window'&&c.fail_policy==='closed'&&c.instances===2&&c.rps===20&&c.legitimate_rps===20&&c.duration_seconds===30&&c.limit===20&&c.window_ms===1000&&c.backend_capacity===4&&c.backend_service_ms===50;
  save('g3-ui-request.json',{at:new Date().toISOString(),valid:good,request:r});
  if(!good){await route.abort();throw Error('UI request outside authorized case')}
  return route.continue();
 });
 await page.goto('http://127.0.0.1:8090',{waitUntil:'domcontentloaded'});
 await page.locator('#preset').selectOption('custom');
 for(const [id,v] of Object.entries({profile:'normal',mode:'redis',algorithm:'fixed-window',failPolicy:'closed',instances:'2'}))await page.locator('#'+id).selectOption(v);
 for(const [id,v] of Object.entries({totalRps:'20',duration:'30',limit:'20',windowMs:'1000',backendCapacity:'4',backendService:'50',repetitions:'1'}))await page.locator('#'+id).fill(v);
 await page.locator('#monitoring').check();
 await page.screenshot({path:out+'/g3-console-config.png',fullPage:true});
 fs.writeFileSync(out+'/g3-attempt.json',JSON.stringify({attempt:1,maximum:1,submitted_utc:new Date().toISOString(),action:'existing Console Chạy benchmark UI; no retries'},null,2)+'\n',{flag:'wx'});
 const response=page.waitForResponse(r=>r.url().endsWith('/api/runs')&&r.request().method()==='POST',{timeout:20000});
 await page.locator('#run').click();
 const res=await response;const body=await res.json();save('g3-submit-response.json',{status:res.status(),body});
 if(!res.ok()||!body.id)throw Error('Sole UI submission failed; no retry');
 const id=body.id;let activeCaptured=false;let graph=null;
 const timeline=[];const stop=Date.now()+300000;
 while(Date.now()<stop){
  const data=await get('http://127.0.0.1:8090/api/runs/'+id);
  const targets=await get('http://127.0.0.1:19090/api/v1/targets');
  const research=targets.data.activeTargets.filter(t=>t.labels.job==='project3-console-run');
  timeline.push({utc:new Date().toISOString(),state:data.run.state,phase:data.phase,targets:research.map(t=>({labels:t.labels,health:t.health,lastScrape:t.lastScrape,lastError:t.lastError,scrapeUrl:t.scrapeUrl}))});
  if(research.length===3&&research.every(t=>t.health==='up')){
   const qs={};for(const expr of ['project3_api_requests_total{job="project3-console-run"}','project3_backend_arrivals_total{job="project3-console-run"}','up{job="project3-demo"}'])qs[expr]=await get('http://127.0.0.1:19090/api/v1/query?query='+encodeURIComponent(expr));
   timeline[timeline.length-1].queries=qs;
   if(!activeCaptured){save('g3-active-targets.json',targets);save('g3-active-network.json',JSON.parse(execFileSync('docker',['network','inspect','project3-monitoring-scrape'],{encoding:'utf8',timeout:10000})));activeCaptured=true;}
   if(!graph){graph=await context.newPage();await graph.goto('http://127.0.0.1:13000/d/project3-monitoring-demo/overview?var-job=project3-console-run&var-rate_window=4s&from=now-1m&to=now',{waitUntil:'domcontentloaded',timeout:15000});}
  }
  if(['completed','failed','canceled','interrupted','cleanup-error'].includes(data.run.state)){save('g3-final-run.json',data);break;}
  await new Promise(r=>setTimeout(r,1000));
 }
 save('g3-timeline.json',timeline);
 await page.reload({waitUntil:'domcontentloaded'});await page.waitForTimeout(1600);
 await page.screenshot({path:out+'/g3-console-result.png',fullPage:true});
 save('g3-console-browser.json',{id,posts,errors,stateText:await page.locator('#state').innerText(),links:await page.locator('#state a').evaluateAll(a=>a.map(x=>({href:x.href,text:x.textContent}))),bodyText:(await page.locator('body').innerText()).slice(0,20000)});
 await browser.close();console.log(JSON.stringify({id,posts,activeCaptured,lastState:timeline.at(-1)?.state,errors}));
})().catch(e=>{save('g3-browser-failure.json',{utc:new Date().toISOString(),error:e.message});console.error(e.message);process.exit(1)});
