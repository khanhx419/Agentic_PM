"""Run with the project venv; LangGraph orchestration, loopback HTTP, no mock model."""
import argparse
import json
import secrets
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from config import ROOT, public_settings
from llm import Gemini, ModelError
from pipeline import initial
from workflow import run_step as advance
from governance import scan, qa
from store import Store

# Server phục vụ Web UI và điều phối LangGraph trên localhost
def make_server(port=8767, model=None, store=None):
    app_token = secrets.token_urlsafe(32)
    database = store or Store(ROOT / '.state')
    llm = model or Gemini()
    allowed_hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    allowed_origins = {'http://' + h for h in allowed_hosts}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def headers_common(self):
            # Header bảo mật cơ bản: chặn iframe, chống sniff MIME và no-cache
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy',
                             "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")

        def send(self, status, data, mime='application/json; charset=utf-8'):
            body = json.dumps(data, ensure_ascii=False).encode() if mime.startswith('application/json') else data
            self.send_response(status)
            self.headers_common()
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def valid_host(self):
            return self.headers.get('Host') in allowed_hosts

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {'error': 'Chỉ phục vụ localhost.'})
            parsed = urllib.parse.urlsplit(self.path)

            # Lấy thông tin cấu hình (model, trạng thái API key)
            if parsed.path == '/api/config':
                return self.send(200, {**public_settings(), 'app_token': app_token, 'port': port})

            # Lấy danh sách 6 User Stories mẫu (Muhammad Awais 2026)
            if parsed.path == '/api/sample-stories':
                candidates = [
                    ROOT.parent.parent / 'input_user_stories_mau.json',
                    ROOT / 'input-mau' / 'input_user_stories_mau.json',
                    ROOT.parent.parent / 'Du-an-Smart-PMS-AI' / 'input_user_stories_mau.json',
                ]
                for sample_file in candidates:
                    if sample_file.is_file():
                        return self.send(200, json.loads(sample_file.read_text(encoding='utf-8')))
                return self.send(404, {'error': 'Không tìm thấy file mẫu.'})

            # Lấy dữ liệu phiên làm việc
            if parsed.path in ('/api/session', '/api/export'):
                try:
                    sid = urllib.parse.parse_qs(parsed.query).get('id', [''])[0]
                    state = database.get(sid, self.headers.get('X-Session-Token', ''))
                    return self.send(200, {'session': state})
                except ValueError as error:
                    return self.send(404, {'error': str(error)})

            # Chạy thử trực tiếp mã Frontend (.tsx) vừa được Hub-and-Spoke sinh ra (không cần sửa code)
            if parsed.path.startswith('/preview/'):
                import re, html as html_lib
                story_id = parsed.path[len('/preview/'):].strip('/')
                if not re.fullmatch(r'[A-Za-z0-9_-]+', story_id):
                    return self.send(400, {'error': 'Story ID không hợp lệ.'})
                smart_dir = (ROOT.parent.parent / 'Du-an-Smart-PMS-AI' / 'backend').resolve()
                tsx_file = smart_dir / 'output' / 'stories' / f'{story_id}_impl.tsx'
                if not tsx_file.is_file():
                    return self.send(404, {'error': f'Không tìm thấy tệp giao diện {story_id}_impl.tsx.'})
                raw_code = tsx_file.read_text(encoding='utf-8', errors='replace')
                safe_code_json = json.dumps(raw_code).replace('</', '<\\/')
                title_esc = html_lib.escape(story_id)
                preview_html = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Live Preview · {title_esc}_impl.tsx</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body class="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4">
  <div id="root" class="w-full max-w-md"></div>
  <script>
    (function() {{
      const rawCode = {safe_code_json};
      const origFetch = window.fetch;
      window.fetch = async function(url, options) {{
        if (typeof url === 'string' && (url.startsWith('/api') || url.includes('/login') || url.includes('/auth'))) {{
          await new Promise(r => setTimeout(r, 450));
          let body = {{}};
          try {{ body = JSON.parse(options && options.body || '{{}}'); }} catch(e) {{}}
          return {{
            ok: true,
            status: 200,
            json: async () => ({{
              token: 'jwt_demo_' + Math.random().toString(36).slice(2, 10),
              message: 'Thành công (Mock API)',
              user: {{ email: body.email || 'user@example.com' }}
            }})
          }};
        }}
        return origFetch.apply(this, arguments);
      }};

      try {{
        const compiled = Babel.transform(rawCode, {{
          filename: '{title_esc}_impl.tsx',
          presets: ['env', 'react', 'typescript']
        }}).code;

        const exportsObj = {{}};
        const moduleObj = {{ exports: exportsObj }};
        const requireFn = function(mod) {{
          if (mod === 'react') return window.React;
          if (mod === 'react-dom' || mod === 'react-dom/client') return window.ReactDOM;
          return {{}};
        }};

        new Function('React', 'ReactDOM', 'require', 'exports', 'module', compiled)(
          window.React, window.ReactDOM, requireFn, exportsObj, moduleObj
        );

        const Comp = moduleObj.exports.default
          || Object.values(moduleObj.exports).find(v => typeof v === 'function')
          || Object.values(exportsObj).find(v => typeof v === 'function');

        const {{ useState }} = window.React;
        function PreviewShell() {{
          const [result, setResult] = useState(null);
          return React.createElement('div', {{ className: 'space-y-4' }},
            React.createElement('div', {{ className: 'text-center' }},
              React.createElement('span', {{ className: 'text-xs font-semibold px-3 py-1 rounded-full bg-blue-950 text-blue-300 border border-blue-800' }}, 'Live Preview · Mã gốc từ Hub-and-Spoke'),
              React.createElement('h1', {{ className: 'text-lg font-bold mt-2' }}, '{title_esc}_impl.tsx')
            ),
            result
              ? React.createElement('div', {{ className: 'p-5 bg-slate-900 border border-emerald-700 rounded-xl space-y-2 text-sm' }},
                  React.createElement('div', {{ className: 'text-emerald-400 font-bold' }}, '✅ Thao tác thành công!'),
                  React.createElement('div', {{ className: 'text-xs text-slate-300 break-all' }}, 'Kết quả trả về: ', React.createElement('code', {{ className: 'text-blue-400' }}, String(result))),
                  React.createElement('button', {{
                    onClick: () => setResult(null),
                    className: 'w-full py-2 mt-2 bg-slate-800 hover:bg-slate-700 rounded text-xs font-semibold'
                  }}, 'Thử lại')
                )
              : Comp
                ? React.createElement(Comp, {{
                    onLoginSuccess: (tok) => setResult(tok),
                    onSuccess: (val) => setResult(val || 'OK'),
                    onLoginError: (err) => console.log('Error:', err)
                  }})
                : React.createElement('div', {{ className: 'p-4 bg-rose-950 border border-rose-800 rounded text-rose-200 text-sm' }}, 'Không tìm thấy React Component được export trong tệp.')
          );
        }}

        ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(PreviewShell));
      }} catch (err) {{
        document.getElementById('root').innerHTML =
          '<div class="p-4 bg-rose-950 border border-rose-800 rounded-xl text-rose-200 text-xs"><b>Lỗi chạy thử:</b> ' + String(err.message || err) + '</div>';
      }}
    }})();
  </script>
</body>
</html>"""
                body = preview_html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return

            # Phục vụ file tĩnh giao diện web
            paths = {'/': 'hub.html', '/hub': 'hub.html', '/assets/app.js': 'app.js', '/assets/style.css': 'style.css'}
            if parsed.path not in paths:
                return self.send(404, {'error': 'Không tìm thấy trang.'})
            file = ROOT / 'web' / paths[parsed.path]
            if not file.is_file():
                return self.send(404, {'error': 'Thiếu tài nguyên giao diện.'})
            mime = 'text/javascript; charset=utf-8' if file.suffix == '.js' else 'text/css; charset=utf-8' if file.suffix == '.css' else 'text/html; charset=utf-8'
            self.send(200, file.read_bytes(), mime)

        def do_POST(self):
            if not self.valid_host() or self.headers.get('Origin') not in (*allowed_origins, None):
                return self.send(403, {'error': 'Nguồn yêu cầu không hợp lệ.'})
            if not secrets.compare_digest(self.headers.get('X-App-Token', ''), app_token):
                return self.send(403, {'error': 'Nạp lại trang để nhận mã phiên ứng dụng.'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.send(415, {'error': 'Cần JSON.'})

            try:
                size = int(self.headers.get('Content-Length', '0'))
                max_size = 2_000_000 if self.path in ('/api/parse-file', '/api/full-sdlc') else 80000
                if not 0 < size <= max_size:
                    raise ValueError('Yêu cầu quá dài hoặc rỗng.')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError('Yêu cầu phải là JSON object.')

                # Trích xuất văn bản từ tệp Word (.docx)
                if self.path == '/api/parse-file':
                    import base64, io, zipfile
                    import xml.etree.ElementTree as ET
                    raw_b64 = data.get('content_base64') or ''
                    raw_bytes = base64.b64decode(raw_b64)
                    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                        xml_bytes = zf.read('word/document.xml')
                    tree = ET.fromstring(xml_bytes)
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    lines = []
                    for p in tree.findall('.//w:p', ns):
                        texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
                        line = ''.join(texts).strip()
                        if line:
                            lines.append(line)
                    return self.send(200, {'text': '\n'.join(lines)})

                # Khởi tạo phiên mới
                if self.path == '/api/sessions':
                    state, token = database.create(initial(data.get('kind'), data.get('description'), data.get('initial_code', '')))
                    return self.send(201, {'session': state, 'session_token': token})

                # Cổng kiểm tra tĩnh độc lập
                if self.path == '/api/gate':
                    code = data.get('code')
                    gate = scan(code)
                    tests = qa(code) if isinstance(code, str) and 0 < len(code) <= 12000 else {'pass': False, 'cases': [], 'error': 'Mã không hợp lệ.'}
                    return self.send(200, {'governance': gate, 'qa': tests, 'accepted': gate['pass'] and tests['pass'], 'model_calls': 0})

                # Chạy toàn bộ vòng đời SDLC (Chuẩn Muhammad Awais 2026)
                if self.path == '/api/full-sdlc':
                    epic = data.get('epic') or "Create a user login page with email validation"
                    mode = (data.get('governance_mode') or "STRICT").upper()
                    custom_stories = data.get('custom_stories')

                    import sys, subprocess, os
                    from pathlib import Path

                    smart_dir = (ROOT.parent.parent / 'Du-an-Smart-PMS-AI' / 'backend').resolve()
                    main_py = str(smart_dir / 'main.py')
                    py_bin = sys.executable

                    cmd = [py_bin, main_py, '--mode', 'single', '--governance', mode, '--epic', epic]

                    temp_stories_file = None
                    if custom_stories:
                        (smart_dir / 'output').mkdir(parents=True, exist_ok=True)
                        temp_stories_file = str(smart_dir / 'output' / '_temp_custom_stories.json')
                        with open(temp_stories_file, 'w', encoding='utf-8') as f:
                            json.dump(custom_stories, f, ensure_ascii=False)
                        cmd.extend(['--stories-file', temp_stories_file])

                    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}
                    p = subprocess.run(cmd, cwd=str(smart_dir), env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    if p.returncode != 0:
                        err_detail = (p.stderr or '').strip() or (p.stdout or '').strip()
                        return self.send(500, {'error': f'Lỗi khi chạy SDLC: {err_detail}'})

                    output_dir = smart_dir / 'output'
                    aggregates_file = output_dir / 'aggregates.json'
                    events_file = output_dir / 'events.json'
                    report_file = output_dir / 'BAO_CAO_SDLC_DELIVERABLES.md'

                    metrics = {}
                    if aggregates_file.is_file():
                        metrics = json.loads(aggregates_file.read_text(encoding='utf-8')).get('summary', {})

                    events = []
                    if events_file.is_file():
                        events = json.loads(events_file.read_text(encoding='utf-8'))

                    stories_report_file = output_dir / 'stories_report.json'
                    if stories_report_file.is_file():
                        stories_data = json.loads(stories_report_file.read_text(encoding='utf-8'))
                    else:
                        stories_data = []
                        stories_source = custom_stories
                        if not stories_source:
                            sample_json = smart_dir.parent / 'input_user_stories_mau.json'
                            if sample_json.is_file():
                                stories_source = json.loads(sample_json.read_text(encoding='utf-8'))

                        stories_dir = output_dir / 'stories'
                        for s in (stories_source or []):
                            s_id = s.get('id', 'ST-1')
                            s_type = s.get('type', 'BACKEND')
                            ext = 'tsx' if s_type == 'FRONTEND' else 'py'
                            impl_path = stories_dir / f'{s_id}_impl.{ext}'
                            test_path = stories_dir / f'{s_id}_test.{ext}'
                            code_txt = impl_path.read_text(encoding='utf-8', errors='replace') if impl_path.is_file() else ''
                            test_txt = test_path.read_text(encoding='utf-8', errors='replace') if test_path.is_file() else ''
                            stories_data.append({
                                'id': s_id,
                                'title': s.get('title', ''),
                                'description': s.get('description', ''),
                                'type': s_type,
                                'story_points': s.get('story_points', 3),
                                'status': 'COMPLETED',
                                'ext': ext,
                                'code': code_txt,
                                'tests': test_txt,
                            })

                    markdown_content = ""
                    if report_file.is_file():
                        markdown_content = report_file.read_text(encoding='utf-8')

                    return self.send(200, {
                        'status': 'success',
                        'data': {
                            'epic': epic,
                            'governance_mode': mode,
                            'metrics': metrics,
                            'stories': stories_data,
                            'events': events,
                            'output_directory': str(output_dir)
                        },
                        'markdown': markdown_content,
                        'report_path': str(report_file)
                    })

                # Chuyển bước tiếp theo trong LangGraph
                if self.path == '/api/next':
                    sid = data.get('id')
                    state = database.get(sid, self.headers.get('X-Session-Token', ''))
                    lock = database.lock(sid)
                    if not lock.acquire(blocking=False):
                        return self.send(409, {'error': 'Bước trước đang xử lý, vui lòng chờ.'})
                    try:
                        state = database.get(sid, self.headers.get('X-Session-Token', ''))
                        if data.get('version') != state['version']:
                            return self.send(409, {'error': 'Trạng thái đã thay đổi. Nạp lại phiên trước khi chạy tiếp.', 'session': state})
                        new = advance(state, llm, data.get('confirmed') is True)
                        database.save(new)
                        return self.send(200, {'session': new})
                    except (ValueError, ModelError) as error:
                        state['last_error'] = str(error)[:400]
                        database.save(state)
                        return self.send(400, {'error': state['last_error'], 'session': state})
                    finally:
                        lock.release()

                return self.send(404, {'error': 'Không có endpoint này.'})

            except (ValueError, TypeError, KeyError, RecursionError) as error:
                return self.send(400, {'error': str(error)[:250] or 'Dữ liệu không hợp lệ.'})
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self.send(500, {'error': f'Lỗi xử lý nội bộ: {str(e)}'})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    port = server.server_address[1]
    allowed_hosts.clear()
    allowed_hosts.update({f'127.0.0.1:{port}', f'localhost:{port}'})
    allowed_origins.clear()
    allowed_origins.update({'http://' + h for h in allowed_hosts})
    server.daemon_threads = True
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    try:
        server = make_server(args.port)
    except OSError:
        raise SystemExit('Port đang được sử dụng. Thử: python app.py --port 8768')
    print(f'Hub:  http://127.0.0.1:{args.port}/hub')
    print('Gemini key configured:', public_settings()['configured'])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
