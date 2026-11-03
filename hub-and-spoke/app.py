"""Run python app.py; stdlib only, binds loopback, no mock model in this server."""
import argparse
import json
import secrets
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from config import ROOT,public_settings
from llm import Gemini,ModelError
from pipeline import initial,advance
from governance import scan,qa
from store import Store

# Web chỉ nhận thao tác; quyết định bước và PASS/FAIL nằm ở backend.
def make_server(port=8766,model=None,store=None):
    app_token=secrets.token_urlsafe(32);database=store or Store(ROOT/'.state');llm=model or Gemini()
    allowed_hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
    allowed_origins={'http://'+h for h in allowed_hosts}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass # Request data and session credentials are not printed.
        def headers_common(self):
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY')
            self.send_header('Referrer-Policy','no-referrer');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        def send(self,status,data,mime='application/json; charset=utf-8'):
            body=json.dumps(data,ensure_ascii=False).encode() if mime.startswith('application/json') else data
            self.send_response(status);self.headers_common();self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def valid_host(self):return self.headers.get('Host') in allowed_hosts
        def do_GET(self):
            if not self.valid_host():return self.send(403,{'error':'Chỉ phục vụ localhost.'})
            parsed=urllib.parse.urlsplit(self.path)
            if parsed.path=='/api/config':return self.send(200,{**public_settings(),'app_token':app_token,'port':port})
            if parsed.path in ('/api/session','/api/export'):
                try:
                    sid=urllib.parse.parse_qs(parsed.query).get('id',[''])[0]
                    state=database.get(sid,self.headers.get('X-Session-Token',''))
                    return self.send(200,{'session':state})
                except ValueError as error:return self.send(404,{'error':str(error)})
            paths={'/':'hub.html','/hub':'hub.html','/assets/app.js':'app.js','/assets/style.css':'style.css'}
            if parsed.path not in paths:return self.send(404,{'error':'Không tìm thấy trang.'})
            file=ROOT/'web'/paths[parsed.path]
            if not file.is_file():return self.send(404,{'error':'Thiếu tài nguyên giao diện.'})
            mime='text/javascript; charset=utf-8' if file.suffix=='.js' else 'text/css; charset=utf-8' if file.suffix=='.css' else 'text/html; charset=utf-8'
            self.send(200,file.read_bytes(),mime)
        def do_POST(self):
            if not self.valid_host() or self.headers.get('Origin') not in (*allowed_origins,None):return self.send(403,{'error':'Nguồn yêu cầu không hợp lệ.'})
            if not secrets.compare_digest(self.headers.get('X-App-Token',''),app_token):return self.send(403,{'error':'Nạp lại trang để nhận mã phiên ứng dụng.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'Cần JSON.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=80000:raise ValueError('Yêu cầu quá dài hoặc rỗng.')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError('Yêu cầu phải là JSON object.')
                if self.path=='/api/sessions':
                    state,token=database.create(initial(data.get('kind'),data.get('description'),data.get('initial_code','')))
                    return self.send(201,{'session':state,'session_token':token})
                if self.path=='/api/gate':
                    code=data.get('code')
                    gate=scan(code)
                    tests=qa(code) if isinstance(code,str) and 0<len(code)<=12000 else {'pass':False,'cases':[],'error':'Mã không hợp lệ.'}
                    return self.send(200,{'governance':gate,'qa':tests,'accepted':gate['pass'] and tests['pass'],'model_calls':0})
                if self.path=='/api/next':
                    sid=data.get('id');state=database.get(sid,self.headers.get('X-Session-Token',''))
                    lock=database.lock(sid)
                    if not lock.acquire(blocking=False):return self.send(409,{'error':'Bước trước đang xử lý, vui lòng chờ.'})
                    try:
                        state=database.get(sid,self.headers.get('X-Session-Token',''))
                        if data.get('version')!=state['version']:return self.send(409,{'error':'Trạng thái đã thay đổi. Nạp lại phiên trước khi chạy tiếp.','session':state})
                        new=advance(state,llm,data.get('confirmed') is True);database.save(new)
                        return self.send(200,{'session':new})
                    except (ValueError,ModelError) as error:
                        state['last_error']=str(error)[:400];database.save(state)
                        return self.send(400,{'error':state['last_error'],'session':state})
                    finally:lock.release()
                return self.send(404,{'error':'Không có endpoint này.'})
            except (ValueError,TypeError,KeyError,RecursionError) as error:return self.send(400,{'error':str(error)[:250] or 'Dữ liệu không hợp lệ.'})
            except Exception:return self.send(500,{'error':'Lỗi xử lý nội bộ; phiên không được tự coi là thành công.'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    port=server.server_address[1]
    allowed_hosts.clear();allowed_hosts.update({f'127.0.0.1:{port}',f'localhost:{port}'})
    allowed_origins.clear();allowed_origins.update({'http://'+h for h in allowed_hosts})
    server.daemon_threads=True
    return server

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);args=parser.parse_args()
    try:server=make_server(args.port)
    except OSError:raise SystemExit('Port dang duoc su dung. Thu: python app.py --port 8767')
    print(f'Hub:  http://127.0.0.1:{args.port}/hub')
    print('Gemini key configured:',public_settings()['configured'])
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
