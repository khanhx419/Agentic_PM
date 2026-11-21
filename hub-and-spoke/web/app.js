'use strict';

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);

let config = null;
let busy = false;
let error = '';
let loadedStories = null;
let loadedFileName = '';
let latestMarkdown = '';
let sdlcResult = null;

async function api(path, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 165000);
  try {
    const headers = {'X-App-Token': config?.app_token || ''};
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

function showSelectedFile(fileName, stories) {
  loadedFileName = fileName;
  loadedStories = stories;
  $('selected-file-name').textContent = '📄 Tệp đã chọn: ' + fileName;
  $('selected-file-count').textContent = stories.length + ' User Stories';
  $('selected-stories-preview').innerHTML = stories.map(s =>
    '<li><b>' + esc(s.id || 'ST') + '</b>: ' + esc(s.title) +
    ' <span class="muted">(' + esc(s.type || 'BACKEND') + ' · ' + esc(s.story_points || 3) + ' pts)</span></li>'
  ).join('');
  $('selected-file-box').hidden = false;
  $('no-file-hint').hidden = true;
  error = '';
  render();
}

function renderOutput(data) {
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

function render() {
  $('connection').textContent = config ? 'Máy chủ sẵn sàng · Cổng ' + config.port : 'Đang kết nối máy chủ…';
  $('error').textContent = error;
  $('error').hidden = !error;

  const hasFile = Array.isArray(loadedStories) && loadedStories.length > 0;
  $('btn-run').disabled = busy || !hasFile;
  $('btn-run').textContent = busy ? '⏳ Đang chạy quy trình SDLC…' : '▶️ Chạy quy trình SDLC';

  for (const id of ['btn-pick-file', 'btn-load-sample-stories', 'btn-download-sample', 'btn-reset', 'gov-mode']) {
    const el = $(id);
    if (el) el.disabled = busy;
  }

  $('btn-download-md').hidden = !latestMarkdown;

  if (busy) {
    $('status').textContent = '🚀 Coordinator đang điều phối các Spoke (Dev FE/BE ➔ QA ➔ PM Governance)…';
  } else if (sdlcResult) {
    $('status').textContent = '✅ Đã hoàn thành toàn bộ quy trình SDLC cho tệp ' + loadedFileName + '.';
    renderOutput(sdlcResult);
  } else {
    $('status').textContent = hasFile
      ? 'Đã sẵn sàng. Bấm "Chạy quy trình SDLC" để bắt đầu.'
      : 'Chọn tệp User Story và bấm Chạy để xem kết quả toàn bộ vòng đời SDLC.';
    $('output').innerHTML = '';
    $('history-panel').hidden = true;
  }
}

// 1. Chọn tệp User Story (.json) từ máy tính
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
      const parsed = JSON.parse(e.target.result);
      const stories = Array.isArray(parsed) ? parsed : parsed.stories;
      if (!Array.isArray(stories) || stories.length === 0) {
        throw new Error('Tệp JSON cần chứa một mảng các User Stories.');
      }
      sdlcResult = null;
      latestMarkdown = '';
      showSelectedFile(file.name, stories);
    } catch (err) {
      error = 'Không đọc được tệp ' + file.name + ': ' + err.message;
      render();
    }
  };
  reader.readAsText(file);
});

// 2. Nạp nhanh 6 User Stories mẫu từ server
$('btn-load-sample-stories').addEventListener('click', async () => {
  try {
    const stories = await api('/api/sample-stories');
    sdlcResult = null;
    latestMarkdown = '';
    showSelectedFile('input_user_stories_mau.json (mẫu sẵn)', stories);
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

// 4. Chạy quy trình Full SDLC
$('demo-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || !loadedStories) return;

  busy = true;
  error = '';
  sdlcResult = null;
  latestMarkdown = '';
  render();

  try {
    config = await api('/api/config');
    const res = await api('/api/full-sdlc', {
      epic: 'User Stories từ ' + loadedFileName,
      governance_mode: $('gov-mode').value,
      custom_stories: loadedStories,
    });
    sdlcResult = res.data;
    latestMarkdown = res.markdown || '';
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
  sdlcResult = null;
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
