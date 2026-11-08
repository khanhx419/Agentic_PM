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

function statusText() {
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

const phaseExplanations = {
  ready: 'Planner đọc yêu cầu và xác định hàm phải đáp ứng những điều kiện nào.',
  planned: 'Developer nhận kế hoạch. Nếu bạn đã nhập mã mẫu, hệ thống dùng mã đó cho lần kiểm tra đầu.',
  coded: 'QA thử hành vi của hàm. Governance đọc cấu trúc mã để tìm vi phạm như secret viết cứng.',
  blocked: 'Hub chuyển lỗi cho Developer. Bản sửa phải qua lại cả hai cổng.',
  review: 'Cả hai cổng đã đạt. Bạn xem mã cuối và quyết định chấp nhận.',
  accepted: 'Bạn đã xác nhận mã sau khi xem kết quả của hai cổng.',
};

const actorExplanations = {
  'Planner → Coordinator': 'Xác định hàm cần làm gì và tiêu chí để kiểm tra.',
  'Người dùng → Coordinator': 'Đưa mã mẫu vào phiên hoặc xác nhận kết quả ở bước cuối.',
  'Developer → Coordinator': 'Nộp bản mã mới hoặc sửa theo lỗi từ lần kiểm tra trước.',
  'QA → Coordinator': 'Kiểm tra hàm trả kết quả đúng với các ca email đã định.',
  'Governance → Coordinator': 'Kiểm tra quy tắc trên cấu trúc mã, ví dụ cấm viết cứng secret.',
  'Coordinator': 'Dừng phiên khi đã dùng hết số lần sửa.',
};

function render() {
  $('status').textContent = statusText();
  const explanation = session?.status === 'exhausted'
    ? 'Bạn có thể mở lịch sử để xem từng bản mã và lý do bị chặn.'
    : phaseExplanations[session?.phase] || '';
  $('step-explanation').textContent = explanation;
  $('step-explanation').hidden = !explanation;
  $('connection').textContent = config?.configured
    ? config.orchestrator + ' · ' + config.model
    : 'Gemini chưa sẵn sàng. Kiểm tra server hoặc chạy cau-hinh-api.cmd.';
  $('error').textContent = error;
  $('error').hidden = !error;
  $('next').disabled = busy;
  $('next').textContent = busy ? 'Đang chạy…' : error && canAdvance() ? 'Tiếp tục phiên' : 'Chạy yêu cầu';
  $('accept').hidden = session?.phase !== 'review';
  $('accept').disabled = busy;
  for (const id of ['request', 'initial-code', 'sample-request', 'sample-code', 'new-request']) $(id).disabled = busy;
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
    '<li><b>' + esc(event.actor) + '</b> · ' + esc(event.message) +
    (actorExplanations[event.actor] ? '<p class="muted">' + esc(actorExplanations[event.actor]) + '</p>' : '') + '</li>'
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

$('demo-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  const request = $('request').value.trim();
  if (request.length < 20) {
    error = 'Nhập yêu cầu có ít nhất 20 ký tự.';
    render();
    return;
  }
  busy = true;
  const resume = error && canAdvance() && session.description === request &&
    session.initial_code === $('initial-code').value;
  error = '';
  render();
  try {
    config = await api('/api/config');
    if (!config.configured) throw new Error('Chưa có Gemini API key. Chạy cau-hinh-api.cmd rồi thử lại.');
    if (!resume) {
      const created = await api('/api/sessions', {
        kind: 'hub', description: request, initial_code: $('initial-code').value,
      });
      session = created.session;
      sessionToken = created.session_token;
      remember();
    }
    $('history-panel').open = true;
    render();
    while (canAdvance()) await advance();
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
  $('demo-form').reset();
  $('code-options').open = false;
  $('history-panel').open = false;
  render();
  $('request').focus();
});

$('sample-request').addEventListener('click', () => {
  $('request').value = sampleRequest;
  $('initial-code').value = '';
  $('request').focus();
});

$('sample-code').addEventListener('click', () => {
  $('request').value = sampleRequest;
  $('initial-code').value = sampleCode;
  $('code-options').open = true;
});

$('export').addEventListener('click', () => {
  if (!session) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(session, null, 2)], {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'hub-session.json';
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
