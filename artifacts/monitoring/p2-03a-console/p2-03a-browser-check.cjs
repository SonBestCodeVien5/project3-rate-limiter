const fs = require('fs');
const {chromium} = require('/home/khanhson2005/.npm/_npx/c44bce6a2a6e9da9/node_modules/playwright');
const out = process.cwd() + '/artifacts/monitoring/p2-03a-console';
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'/home/khanhson2005/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome', args:['--no-sandbox']});
  const context = await browser.newContext({viewport:{width:1440,height:1100}});
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const errors=[]; page.on('pageerror', e => errors.push(e.message));
  await page.goto('http://127.0.0.1:13000/login', {waitUntil:'domcontentloaded', timeout:20000});
  await page.getByRole('button',{name:'Log in',exact:true}).waitFor();
  {
    await page.getByRole('textbox').first().fill('admin');
    await page.locator('input[type="password"]').fill(fs.readFileSync('.secrets/grafana_admin_password','utf8').trim());
    await page.getByRole('button',{name:'Log in',exact:true}).click();
    await page.waitForURL(u => !u.pathname.includes('/login'), {timeout:20000});
  }
  await page.goto('http://127.0.0.1:13000/dashboards',{waitUntil:'domcontentloaded'});
  await page.waitForTimeout(4000); fs.writeFileSync(out+'/grafana-list-body.txt',await page.locator('body').innerText()); await page.screenshot({path:out+'/grafana-list-debug.png',fullPage:true}); await page.getByText('Project 3 Monitoring',{exact:true}).first().waitFor();
  await page.screenshot({path:out+'/grafana-list.png',fullPage:true});
  const folder=page.getByText('Project 3 Monitoring',{exact:true}).first();
  await folder.click();
  await page.waitForTimeout(1200);
  await page.screenshot({path:out+'/grafana-folder.png',fullPage:true});
  await context.storageState({path:'/tmp/p2-03a-browser-auth-private.json'});
  fs.chmodSync('/tmp/p2-03a-browser-auth-private.json',0o600);
  const folderText=(await page.locator('body').innerText()).slice(0,10000);
  await page.goto('http://127.0.0.1:8090',{waitUntil:'domcontentloaded'});
  await page.locator('#run').waitFor();
  const form={monitoring:await page.locator('#monitoring').count(),runText:await page.locator('#run').innerText()};
  await page.screenshot({path:out+'/console-before.png',fullPage:false});
  fs.writeFileSync(out+'/local-browser-g2.json',JSON.stringify({checked_utc:new Date().toISOString(),errors,folderText,form,mcp_failure:'browser MCP stalled; local Playwright used; no workload submitted'},null,2)+'\n');
  await browser.close();
  console.log(JSON.stringify({local_browser:'pass',errors,form}));
})().catch(e=>{console.error(e.message);process.exit(1)});
