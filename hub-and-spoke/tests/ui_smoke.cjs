// Test fixture only: no real LLM calls. Set PLAYWRIGHT_MODULE if playwright is elsewhere.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { spawn } = require('node:child_process');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', 'Scripts', 'python.exe');
(async () => {
  const child = spawn(python, [path.join(__dirname, 'ui_fixture_server.py')], {cwd: root, windowsHide: true, stdio: ['pipe','pipe','pipe']});
  let browser;
  try {
    const url = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Fixture startup timed out')), 60000);
      let stdout = '';
      child.stdout.on('data', data => {stdout += data.toString(); const match = stdout.match(/http:\/\/127\.0\.0\.1:\d+/); if(match){clearTimeout(timer);resolve(match[0]);}});
      child.once('exit', code => {clearTimeout(timer); reject(new Error('Fixture exited: '+code));});
    });
    browser = await chromium.launch({channel: 'msedge', headless: true});
    const page = await browser.newPage({viewport:{width:1440,height:1080}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url+'/hub');
    await page.locator('#connection').filter({hasText:'TEST_DOUBLE'}).waitFor();
    await page.locator('#sample-request').click();
    assert.match(await page.locator('#request').inputValue(), /validate_email/);
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Chờ bạn chấp nhận'}).waitFor();
    assert.match(await page.locator('#history').innerText(), /FAIL/);
    assert.match(await page.locator('#output').innerText(), /r2/);
    assert.match(await page.locator('#output').innerText(), /14\/14/);
    assert.equal(await page.locator('#accept').isVisible(), true);
    await page.locator('#accept').click();
    await page.locator('#status').filter({hasText:'Đã chấp nhận'}).waitFor();
    await page.reload();
    await page.locator('#status').filter({hasText:'Đã chấp nhận'}).waitFor();
    await page.locator('details.history summary').click();
    const result = await page.evaluate(async () => {
      const saved=JSON.parse(sessionStorage.getItem('real-agent-demo-hub'));
      const data=await fetch('/api/session?id='+saved.id,{headers:{'X-Session-Token':saved.token}}).then(r=>r.json());
      return {engine:data.session.engine,status:data.session.status,steps:data.session.graph_steps,calls:data.session.calls.length};
    });
    assert.equal(result.engine,'LangGraph'); assert.equal(result.status,'accepted');
    assert.deepEqual(errors,[]);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1),true);
    console.log('UI smoke passed (fake LLM, real LangGraph/AST/QA).');
  } finally {
    if(browser) await browser.close();
    child.stdin.end('\n');
    await new Promise(resolve => {if(child.exitCode!==null)return resolve(); child.once('exit',resolve);setTimeout(()=>{if(child.exitCode===null)child.kill();resolve();},5000).unref();});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
