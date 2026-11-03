// Test fixture only: no real LLM calls. Set PLAYWRIGHT_MODULE if playwright is elsewhere.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
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
    await page.locator('#connection').filter({hasText:'key đã cấu hình'}).waitFor();
    assert.equal(await page.locator('button:visible').count(),1);
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Planner đã tạo story'}).waitFor();
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Mã đã được nộp'}).waitFor();
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Cổng kiểm tra đang chặn mã'}).waitFor();
    assert.match(await page.locator('#output').innerText(),/HARDCODED_SECRET/);
    const folder = path.join(root,'verification'); fs.mkdirSync(folder,{recursive:true});
    await page.screenshot({path:path.join(folder,'ui-blocked-test-fixture.png'),fullPage:true});
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Mã đã được nộp'}).waitFor();
    await page.locator('#next').click();
    await page.locator('#status').filter({hasText:'Mã đã qua các kiểm tra'}).waitFor();
    await page.locator('#next').click();
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
    await page.screenshot({path:path.join(folder,'ui-accepted-test-fixture.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1),true);
    fs.writeFileSync(path.join(folder,'ui-summary.json'), JSON.stringify({llm:'TEST DOUBLE',langgraph:'REAL',qa_ast:'REAL',browser:'Edge',checks:['one visible primary button','secret blocked','repair and recheck','human accept','reload restores session','no page errors','mobile fits viewport'],...result},null,2));
    console.log('UI smoke passed (fake LLM, real LangGraph/AST/QA).');
  } finally {
    if(browser) await browser.close();
    child.stdin.end('\n');
    await new Promise(resolve => {if(child.exitCode!==null)return resolve(); child.once('exit',resolve);setTimeout(()=>{if(child.exitCode===null)child.kill();resolve();},5000).unref();});
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
