'use strict';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);

let config = null;
let session = null;
let sessionToken = '';
let busy = false;
let error = '';
let loadedStories = null;
let loadedFileName = '';
let loadedRawText = '';
let latestMarkdown = '';
let sdlcResult = null;

async function api(path, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 165000);
  try {
    const headers = {'X-App-Token': config?.app_token || '', 'X-Session-Token': sessionToken};
    const options = {headers, signal: controller.signal};
    if (data !== undefined) {
      options.method = 'POST';
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(data);
    }
    const response = await fetch(path, options);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Yêu cầu thất bại.');
    return result;
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('Hết thời gian chờ xử lý.');
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// Chấp nhận mọi định dạng tệp (.json, .txt, .md, .csv, ...)
function parseAnyFile(fileName, text) {
  const trimmed = (text || '').trim();
  if (!trimmed) throw new Error('Tệp rỗng, không có nội dung.');

  // 1. Thử đọc dạng JSON User Stories
  try {
    const parsed = JSON.parse(trimmed);
    const arr = Array.isArray(parsed) ? parsed : parsed?.stories;
    if (Array.isArray(arr) && arr.length > 0 && typeof arr[0] === 'object') {
      return arr.map((item, idx) => ({
        id: item.id || ('ST-' + (idx + 1)),
        title: item.title || item.description || ('Story ' + (idx + 1)),
        description: item.description || item.title || '',
        type: (item.type || (idx % 2 === 0 ? 'BACKEND' : 'FRONTEND')).toUpperCase(),
        story_points: Number(item.story_points || item.points || 3),
      }));
    }
  } catch (_) {
    // Không phải JSON -> chuyển sang tách dòng văn bản tự do
  }

  // 2. Tách từng dòng / gạch đầu dòng trong tệp văn bản bất kỳ (.txt, .md, .csv, ...)
  const lines = trimmed
    .split(/\r?\n/)
    .map(l => l.replace(/^\s*(?:[-*•]+|\d+[.)])\s*/, '').trim())
    .filter(l => l.length > 0 && !l.startsWith('#'));

  const items = lines.length > 0 ? lines : [trimmed];
  const fePattern = /frontend|ui|form|react|giao di[eệ]n|trang|nút|hi[eể]n th[iị]|view|component|css|html/i;

  return items.slice(0, 20).map((line, idx) => ({
    id: 'ST-' + (idx + 1),
    title: line.length > 90 ? line.slice(0, 87) + '...' : line,
    description: line,
    type: fePattern.test(line) ? 'FRONTEND' : 'BACKEND',
    story_points: 3,
  }));
}

function showSelectedFile(fileName, stories, rawText) {
  loadedFileName = fileName;
  loadedStories = stories;
  loadedRawText = rawText || stories.map(s => s.id + ': ' + s.title + ' - ' + s.description).join('\n');
  $('selected-file-name').textContent = '📄 Tệp đã chọn: ' + fileName;
  $('selected-file-count').textContent = stories.length + ' User Stories';
  $('selected-stories-preview').innerHTML = stories.map(s =>
    '<li><b>' + esc(s.id) + '</b>: ' + esc(s.title) +
    ' <span class="muted">(' + esc(s.type) + ' · ' + esc(s.story_points) + ' pts)</span></li>'
  ).join('');
  $('selected-file-box').hidden = false;
  $('no-file-hint').hidden = true;
  error = '';
  render();
}

function renderFullSdlc(data) {
  const m = data.metrics || {};
  const stories = data.stories || [];

  let html = '<div style="background: #eef5fc; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; border: 1px solid #c2dbf2;">';
  html += '<h3 style="margin-top: 0; color: #1c4b75;">📊 Chỉ số Khoa học SDLC (KPIs · Chế độ ' + esc(data.governance_mode) + ')</h3>';
  html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .7rem; margin-top: .5rem;">';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Agentic Velocity:</b><br><span style="font-size: 1.1rem; color: #14603b; font-weight: bold;">' + esc(m.agentic_velocity_features_per_hour) + '</span> feat/hr</div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Self-Correction (SCR):</b><br><span style="font-size: 1.1rem; color: #9e271a; font-weight: bold;">' + esc(m.self_correction_ratio) + '</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Gov Overhead (GO):</b><br><span style="font-size: 1.1rem; color: #215991; font-weight: bold;">' + esc(m.governance_overhead_seconds) + 's</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>QA Pass Rate:</b><br><span style="font-size: 1.1rem; color: #14603b; font-weight: bold;">' + esc(m.qa_pass_rate_percent) + '%</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Gov Pass Rate:</b><br><span style="font-size: 1.1rem; color: #14603b; font-weight: bold;">' + esc(m.governance_pass_rate_percent) + '%</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Hoàn thành:</b><br><span style="font-size: 1.1rem; font-weight: bold;">' + esc(m.stories_completed) + '/' + stories.length + ' stories</span></div>';
  html += '</div></div>';

  html += '<h3>📋 Kết quả xử lý từng User Story</h3>';
  html += '<table style="width: 100%; border-collapse: collapse; margin-top: .4rem; font-size: .88rem;">';
  html += '<tr style="background: #f0f4f8; text-align: left; border-bottom: 2px solid #d9e2eb;">';
  html += '<th style="padding: .45rem;">ID</th><th style="padding: .45rem;">Tiêu đề</th><th style="padding: .45rem;">Miền</th><th style="padding: .45rem;">Điểm</th><th style="padding: .45rem;">Trạng thái</th></tr>';

  for (const s of stories) {
    const isFe = s.type === 'FRONTEND';
    html += '<tr style="border-bottom: 1px solid #e1e8ed;">';
    html += '<td style="padding: .45rem;"><b>' + esc(s.id) + '</b></td>';
    html += '<td style="padding: .45rem;">' + esc(s.title) + '</td>';
    html += '<td style="padding: .45rem;"><span style="padding: 2px 6px; border-radius: 3px; font-size: .78rem; background: ' + (isFe ? '#e8f0fe' : '#fef7e0') + '; color: ' + (isFe ? '#1a73e8' : '#b06000') + ';">' + esc(s.type) + '</span></td>';
    html += '<td style="padding: .45rem;">' + esc(s.story_points) + ' pts</td>';
    html += '<td style="padding: .45rem;"><b class="pass">' + esc(s.status) + '</b></td>';
    html += '</tr>';
  }
  html += '</table>';

  $('output').innerHTML = html;
  const events = data.events || [];
  $('history-panel').hidden = events.length === 0;
  $('history').innerHTML = events.map(ev =>
    '<li><b>[' + esc(ev.type) + ']</b> · ' + esc(ev.message) + ' <span class="muted">(' + esc(ev.datetime) + ')</span></li>'
  ).join('');
}

function buildMicroMarkdown(s) {
  const lines = ['# BÁO CÁO MICRO HUB-AND-SPOKE (LANGGRAPH)', ''];
  lines.push('**Tệp đầu vào:** ' + loadedFileName);
  if (s.story) {
    lines.push('', '## 1. Kế hoạch (Planner)', '- **Tiêu đề:** ' + s.story.title);
    (s.story.acceptance || []).forEach(a => lines.push('- ' + a));
  }
  if (s.code) {
    lines.push('', '## 2. Mã nguồn (Developer · r' + s.revision + ')', '```python', s.code, '```');
  }
  if (s.qa || s.governance) {
    lines.push('', '## 3. Kiểm thử & Quản trị',
      '- **QA:** ' + (s.qa?.pass ? 'PASS' : 'FAIL'),
      '- **Governance AST:** ' + (s.governance?.pass ? 'PASS' : 'FAIL'));
  }
  return lines.join('\n');
}

function renderMicroHub(s) {
  let html = '';
  if (s.story) {
    html += '<h3>Kế hoạch (Planner)</h3><p>' + esc(s.story.title) + '</p><ul>' +
      (s.story.acceptance || []).map(item => '<li>' + esc(item) + '</li>').join('') + '</ul>';
  }
  if (s.code) {
    html += '<h3>Mã Python · r' + esc(s.revision) + '</h3><pre><code>' + esc(s.code) + '</code></pre>';
  }
  if (s.qa || s.governance) {
    html += '<div class="check"><span>QA</span><b class="' + (s.qa?.pass ? 'pass' : 'fail') + '">' + (s.qa?.pass ? 'PASS' : 'FAIL') + '</b></div>';
    html += '<div class="check"><span>Governance AST</span><b class="' + (s.governance?.pass ? 'pass' : 'fail') + '">' + (s.governance?.pass ? 'PASS' : 'FAIL') + '</b></div>';
  }
  $('output').innerHTML = html;
  const events = s.events || [];
  $('history-panel').hidden = events.length === 0;
  $('history').innerHTML = events.map(ev =>
    '<li><b>' + esc(ev.actor) + '</b> · ' + esc(ev.message) + '</li>'
  ).join('');
}

function render() {
  $('connection').textContent = config ? 'Máy chủ sẵn sàng · Cổng ' + config.port : 'Đang kết nối máy chủ…';
  $('error').textContent = error;
  $('error').hidden = !error;

  const isFull = $('execution-mode').value === 'full-sdlc';
  $('gov-container').style.display = isFull ? 'block' : 'none';

  const hasFile = Array.isArray(loadedStories) && loadedStories.length > 0;
  $('btn-run').disabled = busy || !hasFile;
  $('btn-run').textContent = busy ? '⏳ Đang chạy quy trình…' : '▶️ Chạy quy trình';

  for (const id of ['btn-pick-file', 'btn-load-sample-stories', 'btn-download-sample', 'btn-reset', 'execution-mode', 'gov-mode']) {
    const el = $(id);
    if (el) el.disabled = busy;
  }

  $('btn-download-md').hidden = !latestMarkdown;

  if (busy) {
    $('status').textContent = isFull
      ? '🚀 Coordinator đang điều phối các Spoke (Dev FE/BE ➔ QA ➔ PM Governance)…'
      : '⚡ LangGraph đang chạy từng bước Hub-and-Spoke…';
  } else if (sdlcResult) {
    $('status').textContent = '✅ Đã hoàn thành toàn bộ quy trình SDLC cho tệp ' + loadedFileName + '.';
    renderFullSdlc(sdlcResult);
  } else if (session) {
    $('status').textContent = '✅ Hoàn thành Micro Hub-and-Spoke (' + session.phase + ').';
    renderMicroHub(session);
  } else {
    $('status').textContent = hasFile
      ? 'Đã sẵn sàng. Chọn chế độ và bấm "Chạy quy trình".'
      : 'Chọn tệp đầu vào và bấm Chạy để bắt đầu.';
    $('output').innerHTML = '';
    $('history-panel').hidden = true;
  }
}

$('execution-mode').addEventListener('change', render);

// 1. Chọn BẤT KỲ tệp nào từ máy tính
$('btn-pick-file').addEventListener('click', () => {
  $('file-picker').value = '';
  $('file-picker').click();
});

$('file-picker').addEventListener('change', event => {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const raw = e.target.result;
      const stories = parseAnyFile(file.name, raw);
      sdlcResult = null;
      session = null;
      latestMarkdown = '';
      showSelectedFile(file.name, stories, raw);
    } catch (err) {
      error = 'Không đọc được tệp ' + file.name + ': ' + err.message;
      render();
    }
  };
  reader.readAsText(file);
});

// 2. Nạp nhanh 6 User Stories mẫu
$('btn-load-sample-stories').addEventListener('click', async () => {
  try {
    const stories = await api('/api/sample-stories');
    sdlcResult = null;
    session = null;
    latestMarkdown = '';
    showSelectedFile('input_user_stories_mau.json (mẫu sẵn)', stories, JSON.stringify(stories, null, 2));
  } catch (err) {
    error = 'Không nạp được tệp mẫu: ' + err.message;
    render();
  }
});

// 3. Tải file mẫu (.json) về máy
$('btn-download-sample').addEventListener('click', async () => {
  try {
    const stories = await api('/api/sample-stories');
    const blob = new Blob([JSON.stringify(stories, null, 2)], {type: 'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'input_user_stories_mau.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (err) {
    error = 'Không tải được tệp mẫu: ' + err.message;
    render();
  }
});

// 4. Chạy quy trình theo chế độ đã chọn
$('demo-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || !loadedStories) return;

  const isFull = $('execution-mode').value === 'full-sdlc';
  busy = true;
  error = '';
  sdlcResult = null;
  session = null;
  latestMarkdown = '';
  render();

  try {
    config = await api('/api/config');
    if (isFull) {
      const res = await api('/api/full-sdlc', {
        epic: 'User Stories từ ' + loadedFileName,
        governance_mode: $('gov-mode').value,
        custom_stories: loadedStories,
      });
      sdlcResult = res.data;
      latestMarkdown = res.markdown || '';
    } else {
      if (!config.configured) throw new Error('Chưa có Gemini API key để chạy chế độ Micro.');
      const desc = loadedRawText.length >= 20 ? loadedRawText.slice(0, 9000) : ('Yêu cầu từ tệp ' + loadedFileName + ': ' + loadedRawText);
      const created = await api('/api/sessions', {kind: 'hub', description: desc, initial_code: ''});
      session = created.session;
      sessionToken = created.session_token;
      while (session && !['review', 'accepted', 'exhausted'].includes(session.status)) {
        const next = await api('/api/next', {id: session.id, version: session.version, confirmed: false});
        session = next.session;
        render();
      }
      latestMarkdown = buildMicroMarkdown(session);
    }
  } catch (err) {
    error = err.message;
  } finally {
    busy = false;
    render();
  }
});

// 5. Tải file Báo cáo Markdown (.md)
$('btn-download-md').addEventListener('click', () => {
  if (!latestMarkdown) return;
  const blob = new Blob([latestMarkdown], {type: 'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'BAO_CAO_SDLC_DELIVERABLES.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

// 6. Làm mới
$('btn-reset').addEventListener('click', () => {
  if (busy) return;
  loadedStories = null;
  loadedFileName = '';
  loadedRawText = '';
  sdlcResult = null;
  session = null;
  latestMarkdown = '';
  error = '';
  $('file-picker').value = '';
  $('selected-file-box').hidden = true;
  $('no-file-hint').hidden = false;
  render();
});

async function boot() {
  try {
    config = await api('/api/config');
  } catch (err) {
    error = 'Không kết nối được máy chủ: ' + err.message;
  }
  render();
}

boot();
