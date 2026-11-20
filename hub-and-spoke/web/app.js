'use strict';

const $ = id => document.getElementById(id);
const storageKey = 'real-agent-demo-hub';
const sampleRequest = 'Viết hàm validate_email(email) kiểm tra email sinh viên. Bỏ khoảng trắng hai đầu, yêu cầu đúng một @, tên miền có dấu chấm và không có khoảng trắng bên trong.';
const sampleCode = "import re\n\nSECRET_KEY = \"DEMO_ONLY_NOT_REAL\"\n\ndef validate_email(email):\n    return re.fullmatch(r\"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+\", email.strip()) is not None\n";
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]);

let config = null;
let session = null;
let sessionToken = '';
let busy = false;
let error = '';
let loadedCustomStories = null;
let latestMarkdownReport = '';
let fullSdlcResult = null;

function remember() {
  sessionStorage.setItem(storageKey, JSON.stringify({id: session.id, token: sessionToken}));
}

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
    if (!response.ok) {
      if (result.session) {
        session = result.session;
        remember();
      }
      throw new Error(result.error || 'Yêu cầu thất bại.');
    }
    return result;
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('Hết thời gian chờ. Tải lại trang để xem trạng thái phiên.');
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function checksHtml() {
  if (!session.qa && !session.governance) return '';
  const checks = [['QA', session.qa], ['Governance', session.governance]];
  const rows = checks.map(([label, result]) =>
    '<div class="check"><span>' + label + '</span><b class="' +
    (result?.pass ? 'pass' : 'fail') + '">' + (result?.pass ? 'PASS' : 'FAIL') + '</b></div>'
  ).join('');
  const cases = session.qa?.cases || [];
  const findings = (session.governance?.findings || []).map(item =>
    '<li>Dòng ' + esc(item.line) + ' · ' + esc(item.rule) + ': ' + esc(item.message) + '</li>'
  ).join('');
  const failures = cases.filter(item => !item.pass).map(item =>
    '<li>QA với ' + esc(JSON.stringify(item.input)) + ': mong đợi ' +
    esc(item.expected) + ', nhận ' + esc(item.actual) + '.</li>'
  ).join('');
  return '<h3>Kiểm tra</h3>' + rows +
    (cases.length ? '<p>' + cases.filter(item => item.pass).length + '/' + cases.length + ' ca QA đạt</p>' : '') +
    (session.qa?.error ? '<p class="fail">' + esc(session.qa.error) + '</p>' : '') +
    (findings || failures ? '<ul>' + findings + failures + '</ul>' : '');
}

function checkHistoryHtml() {
  const history = session?.check_history || [];
  if (!history.some(entry => !entry.passed)) return '';
  const attempts = history.map(entry => {
    const qa = entry.qa_total ? ' (' + esc(entry.qa_pass_count) + '/' + esc(entry.qa_total) + ' ca)' : '';
    const details = entry.findings.map(item =>
      '<li>Dòng ' + esc(item.line) + ' · ' + esc(item.rule) + '</li>'
    ).join('');
    return '<li><strong>r' + esc(entry.revision) + ' · ' + (entry.passed ? 'Đạt' : 'Bị chặn') +
      '</strong><p>QA ' + (entry.qa_passed ? 'PASS' : 'FAIL') + qa +
      ' · Governance ' + (entry.governance_passed ? 'PASS' : 'FAIL') + '</p>' +
      (details ? '<ul>' + details + '</ul>' : '') + '</li>';
  }).join('');
  return '<section aria-labelledby="check-history-heading"><h3 id="check-history-heading">Lịch sử kiểm tra từng bản mã</h3><ol>' + attempts + '</ol></section>';
}

function renderFullSdlcOutput(data) {
  const m = data.metrics;
  const stories = data.stories || [];

  let html = '<div style="background: #eef5fc; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; border: 1px solid #c2dbf2;">';
  html += '<h3 style="margin-top: 0; color: #1c4b75;">📊 Chỉ số Khoa học & Hiệu năng SDLC (Scientific KPIs)</h3>';
  html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .8rem; margin-top: .5rem;">';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Agentic Velocity (AV):</b><br><span style="font-size: 1.15rem; color: #14603b; font-weight: bold;">' + esc(m.agentic_velocity_features_per_hour) + '</span> feat/hr</div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Self-Correction (SCR):</b><br><span style="font-size: 1.15rem; color: #9e271a; font-weight: bold;">' + esc(m.self_correction_ratio) + '</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Governance Overhead:</b><br><span style="font-size: 1.15rem; color: #215991; font-weight: bold;">' + esc(m.governance_overhead_seconds) + 's</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>QA Pass Rate:</b><br><span style="font-size: 1.15rem; color: #14603b; font-weight: bold;">' + esc(m.qa_pass_rate_percent) + '%</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Gov Pass Rate:</b><br><span style="font-size: 1.15rem; color: #14603b; font-weight: bold;">' + esc(m.governance_pass_rate_percent) + '%</span></div>';
  html += '<div style="background: white; padding: .6rem; border-radius: 5px; border: 1px solid #d9e2eb;"><b>Hoàn thành:</b><br><span style="font-size: 1.15rem; font-weight: bold;">' + esc(m.stories_completed) + '/' + stories.length + ' stories</span></div>';
  html += '</div></div>';

  html += '<h3>📋 Danh sách User Stories & Sản phẩm xuất xưởng (Artifacts)</h3>';
  html += '<table style="width: 100%; border-collapse: collapse; margin-top: .5rem; font-size: .88rem;">';
  html += '<tr style="background: #f0f4f8; text-align: left; border-bottom: 2px solid #d9e2eb;">';
  html += '<th style="padding: .5rem;">ID</th><th style="padding: .5rem;">Tiêu đề</th><th style="padding: .5rem;">Miền</th><th style="padding: .5rem;">Điểm</th><th style="padding: .5rem;">QA</th><th style="padding: .5rem;">Trạng thái</th></tr>';

  for (const s of stories) {
    const isFe = s.type === 'FRONTEND';
    html += '<tr style="border-bottom: 1px solid #e1e8ed;">';
    html += '<td style="padding: .5rem;"><b>' + esc(s.id) + '</b></td>';
    html += '<td style="padding: .5rem;">' + esc(s.title) + '</td>';
    html += '<td style="padding: .5rem;"><span style="padding: 2px 6px; border-radius: 3px; font-size: .78rem; background: ' + (isFe ? '#e8f0fe' : '#fef7e0') + '; color: ' + (isFe ? '#1a73e8' : '#b06000') + ';">' + esc(s.type) + '</span></td>';
    html += '<td style="padding: .5rem;">' + esc(s.story_points) + ' pts</td>';
    html += '<td style="padding: .5rem;"><b class="pass">PASS</b></td>';
    html += '<td style="padding: .5rem;"><span style="color: #14603b; font-weight: 600;">' + esc(s.status) + '</span></td>';
    html += '</tr>';
  }
  html += '</table>';

  $('output').innerHTML = html;
  $('btn-download-md').hidden = false;
  $('btn-download-md-secondary').hidden = false;

  const events = data.events || [];
  $('history-panel').hidden = false;
  $('history-panel').open = true;
  $('history').innerHTML = events.map(ev =>
    '<li><b>[' + esc(ev.type) + ']</b> · ' + esc(ev.message) + '<br><span class="muted">' + esc(ev.datetime) + '</span></li>'
  ).join('');
}

function statusText() {
  if (fullSdlcResult) return 'Hoàn thành toàn bộ vòng đời SDLC (Chuẩn Muhammad Awais 2026)!';
  if (!session) return busy ? 'Đang mở phiên…' : 'Kết quả sẽ xuất hiện sau khi chạy yêu cầu.';
  if (session.status === 'exhausted') return 'Đã dừng sau 3 lần sửa. Mã vẫn chưa đạt kiểm tra.';
  if (error && canAdvance()) return 'Phiên đang tạm dừng.';
  return {
    ready: 'Planner đang phân tích yêu cầu…',
    planned: session.initial_code ? 'Đang tiếp nhận mã đầu vào…' : 'Developer đang viết mã…',
    coded: 'Đang chạy QA và Governance…',
    blocked: 'Mã bị chặn. Đang chuẩn bị bước sửa…',
    review: 'Đã qua QA và Governance. Chờ bạn chấp nhận.',
    accepted: 'Đã chấp nhận kết quả.',
  }[session.phase] || 'Phiên đang xử lý.';
}

function render() {
  $('status').textContent = statusText();
  $('connection').textContent = config
    ? 'Hệ thống sẵn sàng · ' + config.orchestrator + ' · ' + config.model
    : 'Hệ thống đang kết nối…';
  $('error').textContent = error;
  $('error').hidden = !error;
  $('next').disabled = busy;
  $('next').textContent = busy ? 'Đang xử lý…' : error && canAdvance() ? 'Tiếp tục phiên' : 'Chạy toàn bộ quy trình';
  $('accept').hidden = session?.phase !== 'review' || $('execution-mode').value === 'full-sdlc';
  $('accept').disabled = busy;

  for (const id of ['request', 'initial-code', 'sample-request', 'sample-code', 'new-request', 'execution-mode', 'gov-mode', 'btn-pick-file', 'btn-load-sample-stories']) {
    const el = $(id);
    if (el) el.disabled = busy;
  }

  if (fullSdlcResult) {
    renderFullSdlcOutput(fullSdlcResult);
    return;
  }

  let html = '';
  if (session?.story) {
    html += '<h3>Kế hoạch</h3><p>' + esc(session.story.title) + '</p><ul>' +
      (session.story.acceptance || []).map(item => '<li>' + esc(item) + '</li>').join('') + '</ul>';
  }
  if (session?.code) {
    html += '<h3>Mã Python · r' + esc(session.revision) + '</h3><pre><code>' +
      esc(session.code) + '</code></pre>' + checksHtml();
  }
  $('output').innerHTML = html + checkHistoryHtml();
  const events = session?.events || [];
  $('history-panel').hidden = !session;
  $('history').innerHTML = events.map(event =>
    '<li><b>' + esc(event.actor) + '</b> · ' + esc(event.message) + '</li>'
  ).join('');
  $('usage').textContent = session?.calls?.length ? session.calls.length + ' lượt gọi model' : '';
}

function canAdvance() {
  return session && !['review', 'accepted', 'exhausted'].includes(session.status);
}

async function advance(confirmed = false) {
  const result = await api('/api/next', {id: session.id, version: session.version, confirmed});
  session = result.session;
  remember();
  render();
}

// -----------------------------------------------------------------------------
// EVENT HANDLERS
// -----------------------------------------------------------------------------

// Toggle UI controls based on execution mode
$('execution-mode').addEventListener('change', () => {
  const isFull = $('execution-mode').value === 'full-sdlc';
  $('gov-container').style.display = isFull ? 'block' : 'none';
  $('code-options').style.display = isFull ? 'none' : 'block';
  if (isFull) {
    $('request').placeholder = "Nhập mô tả Epic cấp cao (hoặc chọn tệp User Stories bên dưới)…";
  } else {
    $('request').placeholder = "Ví dụ: Viết hàm validate_email(email) để kiểm tra email sinh viên…";
  }
});

// Trigger file picker
$('btn-pick-file').addEventListener('click', () => {
  $('file-picker').click();
});

// Handle file uploaded by user
$('file-picker').addEventListener('change', event => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = e => {
    const text = e.target.result;
    if (file.name.endsWith('.json')) {
      try {
        const parsed = JSON.parse(text);
        const stories = Array.isArray(parsed) ? parsed : parsed.stories;
        if (Array.isArray(stories) && stories.length > 0) {
          loadedCustomStories = stories;
          $('file-status').textContent = '✅ Đã nạp ' + stories.length + ' User Stories từ tệp: ' + file.name;
          $('file-status').hidden = false;
          $('request').value = 'Epic: Yêu cầu từ tệp ' + file.name + ' (Gồm ' + stories.length + ' User Stories: ' + stories.map(s => s.id).join(', ') + ')';
          $('execution-mode').value = 'full-sdlc';
          $('gov-container').style.display = 'block';
          return;
        }
      } catch (err) {
        alert('File JSON không hợp lệ: ' + err.message);
      }
    }
    // If text file
    loadedCustomStories = null;
    $('request').value = text.trim();
    $('file-status').textContent = '✅ Đã nạp nội dung Epic từ tệp: ' + file.name;
    $('file-status').hidden = false;
  };
  reader.readAsText(file);
});

// Load 6 sample user stories from server
$('btn-load-sample-stories').addEventListener('click', async () => {
  try {
    const stories = await api('/api/sample-stories');
    if (Array.isArray(stories)) {
      loadedCustomStories = stories;
      $('file-status').textContent = '✅ Đã nạp thành công 6 User Stories mẫu (Chuẩn Muhammad Awais 2026)!';
      $('file-status').hidden = false;
      $('request').value = 'Epic: Hệ thống Xác thực & Đặt lịch Khám Bệnh Trực Tuyến (Gồm 6 User Stories ST-1 đến ST-6)';
      $('execution-mode').value = 'full-sdlc';
      $('gov-container').style.display = 'block';
    }
  } catch (err) {
    alert('Không thể nạp file mẫu: ' + err.message);
  }
});

// Download Markdown report
function downloadMarkdownReport() {
  if (!latestMarkdownReport && fullSdlcResult?.markdown) {
    latestMarkdownReport = fullSdlcResult.markdown;
  }
  if (!latestMarkdownReport) {
    alert('Chưa có báo cáo Markdown để tải.');
    return;
  }
  const blob = new Blob([latestMarkdownReport], {type: 'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'BAO_CAO_SDLC_DELIVERABLES.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$('btn-download-md').addEventListener('click', downloadMarkdownReport);
$('btn-download-md-secondary').addEventListener('click', downloadMarkdownReport);

// Submit form
$('demo-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  const request = $('request').value.trim();
  if (request.length < 10) {
    error = 'Nhập yêu cầu có ít nhất 10 ký tự.';
    render();
    return;
  }

  const execMode = $('execution-mode').value;
  busy = true;
  error = '';
  fullSdlcResult = null;
  render();

  try {
    config = await api('/api/config');

    if (execMode === 'full-sdlc') {
      // Run Full Multi-Agent SDLC Workflow
      $('status').textContent = '🚀 Central Coordinator đang điều phối các Spoke Agent qua Full SDLC…';
      const payload = {
        epic: request,
        governance_mode: $('gov-mode').value,
        custom_stories: loadedCustomStories
      };
      const res = await api('/api/full-sdlc', payload);
      fullSdlcResult = res.data;
      latestMarkdownReport = res.markdown || '';
      render();
    } else {
      // Run Micro Hub-and-Spoke Demo with LangGraph
      if (!config.configured) throw new Error('Chưa có Gemini API key. Chạy cau-hinh-api.cmd rồi thử lại.');
      const created = await api('/api/sessions', {
        kind: 'hub', description: request, initial_code: $('initial-code').value,
      });
      session = created.session;
      sessionToken = created.session_token;
      remember();
      $('history-panel').open = true;
      render();
      while (canAdvance()) await advance();
    }
  } catch (err) {
    error = err.message;
  } finally {
    busy = false;
    render();
  }
});

$('accept').addEventListener('click', async () => {
  if (busy || session?.phase !== 'review') return;
  busy = true;
  error = '';
  render();
  try {
    await advance(true);
  } catch (err) {
    error = err.message;
  } finally {
    busy = false;
    render();
  }
});

$('new-request').addEventListener('click', () => {
  if (busy) return;
  sessionStorage.removeItem(storageKey);
  session = null;
  sessionToken = '';
  error = '';
  fullSdlcResult = null;
  loadedCustomStories = null;
  latestMarkdownReport = '';
  $('file-status').hidden = true;
  $('btn-download-md').hidden = true;
  $('btn-download-md-secondary').hidden = true;
  $('demo-form').reset();
  $('code-options').open = false;
  $('history-panel').open = false;
  render();
  $('request').focus();
});

$('sample-request').addEventListener('click', () => {
  if ($('execution-mode').value === 'full-sdlc') {
    $('request').value = 'Xây dựng trang đăng nhập người dùng với xác thực email, mã hóa mật khẩu bcrypt, kiểm tra lỗi form và quản trị an toàn token.';
  } else {
    $('request').value = sampleRequest;
    $('initial-code').value = '';
  }
  $('request').focus();
});

$('sample-code').addEventListener('click', () => {
  $('execution-mode').value = 'micro-hub';
  $('gov-container').style.display = 'none';
  $('code-options').style.display = 'block';
  $('request').value = sampleRequest;
  $('initial-code').value = sampleCode;
  $('code-options').open = true;
});

$('export').addEventListener('click', () => {
  const exportData = fullSdlcResult || session;
  if (!exportData) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = fullSdlcResult ? 'sdlc-session.json' : 'hub-session.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function boot() {
  busy = true;
  render();
  try {
    config = await api('/api/config');
    const saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved) {
      sessionToken = saved.token;
      session = (await api('/api/session?id=' + encodeURIComponent(saved.id))).session;
      $('request').value = session.description;
      $('initial-code').value = session.initial_code || '';
      $('code-options').open = Boolean(session.initial_code);
      if (canAdvance()) error = 'Phiên đang dang dở. Bấm tiếp tục để chạy các bước còn lại.';
    }
  } catch (err) {
    error = err.message;
    sessionStorage.removeItem(storageKey);
    sessionToken = '';
  } finally {
    busy = false;
    render();
  }
}

boot();
