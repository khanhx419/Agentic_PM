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

                    stories_data = []
                    stories_source = custom_stories
                    if not stories_source:
                        sample_json = smart_dir.parent / 'input_user_stories_mau.json'
                        if sample_json.is_file():
                            stories_source = json.loads(sample_json.read_text(encoding='utf-8'))

                    for s in (stories_source or []):
                        stories_data.append({
                            'id': s.get('id', 'ST-1'),
                            'title': s.get('title', ''),
                            'type': s.get('type', 'BACKEND'),
                            'story_points': s.get('story_points', 3),
                            'status': 'COMPLETED'
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
