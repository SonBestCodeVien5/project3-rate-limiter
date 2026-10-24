const fs=require('fs');
const {chromium}=require('/home/khanhson2005/.npm/_npx/c44bce6a2a6e9da9/node_modules/playwright');
const out=process.cwd()+'/artifacts/monitoring/p2-03a-console';
const dashboard=JSON.parse(fs.readFileSync('deploy/monitoring/grafana/dashboards/project3-overview.json'));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/home/khanhson2005/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome',args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1600,height:1050},storageState:'/tmp/p2-03a-browser-auth-private.json'});
 const page=await context.newPage();page.setDefaultTimeout(15000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const results=[];
 for(const mode of ['fixed','console']){
  if(mode==='console'&&!fs.existsSync(out+'/accepted-monitoring.json'))continue;
  const queries=[];const pending=[];
  page.removeAllListeners('response');page.on('response',r=>{if(r.url().includes('/api/ds/query')&&r.request().method()==='POST')pending.push(r.json().then(j=>{queries.push({status:r.status(),request:r.request().postDataJSON(),response:j})}).catch(e=>queries.push({parseError:e.message})));});
  const url=mode==='fixed'?'http://127.0.0.1:13000/d/project3-monitoring-demo/overview?var-job=project3-demo&var-rate_window=20s&from=now-5m&to=now':JSON.parse(fs.readFileSync(out+'/accepted-monitoring.json')).grafana_url;
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:20000});
  await page.getByText(dashboard.panels[0].title,{exact:true}).first().waitFor();
  const seen=[];
  for(let i=0;i<dashboard.panels.length;i++){
   const panel=page.getByText(dashboard.panels[i].title,{exact:true}).first();
   await panel.scrollIntoViewIfNeeded();await page.waitForTimeout(1200);
   seen.push({id:dashboard.panels[i].id,title:dashboard.panels[i].title,visible:await panel.isVisible()});
   if([0,3,6].includes(i))await page.screenshot({path:out+'/'+mode+'-panels-'+i+'.png'});
  }
  await Promise.allSettled(pending);
  const body=await page.locator('body').innerText();
  fs.writeFileSync(out+'/'+mode+'-grafana-queries.json',JSON.stringify(queries,null,2)+'\n');
  fs.writeFileSync(out+'/'+mode+'-grafana-body.txt',body+'\n');
  results.push({mode,url,seen,queryResponses:queries.length,hasNoData:body.includes('No data'),hasQueryError:body.includes('An error occurred'),errors:[...errors]});
 }
 fs.writeFileSync(out+'/rendered-panels.json',JSON.stringify(results,null,2)+'\n');
 await browser.close();console.log(JSON.stringify(results.map(r=>({mode:r.mode,panels:r.seen.length,queryResponses:r.queryResponses,hasNoData:r.hasNoData,errors:r.errors}))));
})().catch(e=>{console.error(e.message);process.exit(1)});
