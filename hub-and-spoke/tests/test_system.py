import sys,json,unittest,tempfile,threading,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from governance import scan,qa,redact_code
from pipeline import initial,advance
from store import Store
from app import make_server
from llm import Gemini,ModelError

GOOD='import re\nimport os\nSECRET_KEY = os.getenv("SECRET_KEY")\ndef validate_email(email):\n    return re.fullmatch(r"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+", email.strip()) is not None\n'
BAD=GOOD.replace('os.getenv("SECRET_KEY")','"FAKE_DO_NOT_KEEP"')

class FakeModel:
    def __init__(self,bad_schedule=False):self.calls=[];self.bad_schedule=bad_schedule;self.dev_calls=0
    def call(self,role,instruction,payload):
        self.calls.append((role,payload))
        if role=='planner':data={'story':{'title':'Email','acceptance':['valid','invalid']}}
        elif role=='developer':
            if 'trusted_feedback' in payload:
                assert 'FAKE_DO_NOT_KEEP' not in payload['code_to_repair']
                data={'code':GOOD}
            else:data={'code':BAD}
        else:raise AssertionError('Unexpected role: '+role)
        return data,{'role':role,'provider':'TEST DOUBLE','model':'fake','seconds':0,'input_tokens':1,'output_tokens':1}

class GateTests(unittest.TestCase):
    def test_secret_and_environment(self):
        self.assertFalse(scan(BAD)['pass']);self.assertTrue(scan(GOOD)['pass'])
        self.assertNotIn('FAKE_DO_NOT_KEEP',redact_code(BAD))
    def test_concatenated_and_alias_secret(self):
        self.assertFalse(scan('PART="abc"\nAPI_KEY=PART+"xyz"\ndef validate_email(email):\n return True')['pass'])
    def test_environment_fallback_is_blocked(self):self.assertFalse(scan(GOOD.replace('os.getenv("SECRET_KEY")','os.getenv("SECRET_KEY", "bad")'))['pass'])
    def test_import_and_exec_rejected(self):
        self.assertFalse(scan('import subprocess\ndef validate_email(email):\n return bool(email)')['pass'])
        self.assertFalse(scan('def validate_email(email):\n return eval(email)')['pass'])
    def test_real_qa(self):
        result=qa(GOOD);self.assertTrue(result['pass'],result);self.assertEqual(len(result['cases']),14)
        self.assertFalse(qa('def validate_email(email):\n return "@" in email')['pass'])
    def test_unsupported_code_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/'marker.txt'
            code=f'open({str(marker)!r},"w").write("bad")\ndef validate_email(email):\n return True'
            self.assertFalse(qa(code)['pass']);self.assertFalse(marker.exists())


class PipelineTests(unittest.TestCase):
    def test_hub_block_repair_review(self):
        model=FakeModel();s=initial('hub','Implement a simple email validation function.')
        for _ in range(3):s=advance(s,model)
        self.assertEqual(s['phase'],'blocked');self.assertTrue(s['qa']['pass']);self.assertFalse(s['governance']['pass'])
        s=advance(s,model);self.assertIsNone(s['qa']);s=advance(s,model);self.assertEqual(s['phase'],'review')
        with self.assertRaises(ValueError):advance(s,model)
        s=advance(s,model,True);self.assertEqual(s['status'],'accepted')
    def test_failure_preserves_input_state(self):
        class Broken:
            def call(self,*_):raise ModelError('quota')
        s=initial('hub','Implement email validation function please.')
        with self.assertRaises(ModelError):advance(s,Broken())
        self.assertEqual(s['phase'],'ready');self.assertEqual(s['version'],0)
    def test_retry_cap(self):
        s=initial("hub","Implement a simple email validation function.")
        s.update(phase="blocked",status="blocked",repairs=3)
        model=FakeModel();result=advance(s,model)
        self.assertEqual(result["status"],"exhausted");self.assertEqual(model.calls,[])

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.model=FakeModel();self.server=make_server(0,self.model,Store(self.tmp.name));self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base='http://127.0.0.1:'+str(self.server.server_address[1]);self.config=self.request('/api/config')
    def tearDown(self):self.server.shutdown();self.server.server_close();self.tmp.cleanup()
    def request(self,path,data=None,token='',app=True,extra=None):
        headers={'X-App-Token':self.config['app_token'] if app and hasattr(self,'config') else '', 'X-Session-Token':token}
        if extra:headers.update(extra)
        body=None
        if data is not None:body=json.dumps(data).encode();headers['Content-Type']='application/json'
        req=urllib.request.Request(self.base+path,data=body,headers=headers)
        with urllib.request.urlopen(req,timeout=10) as response:return json.load(response)
    def test_config_never_exposes_key(self):
        with patch('config.settings',return_value={'key':'PRIVATE_TEST_KEY','model':'model'}):
            self.assertNotIn('PRIVATE_TEST_KEY',json.dumps(self.request('/api/config')))
    def test_files_are_not_exposed(self):
        for path in ['/.env','/app.py','/.state/sessions.sqlite3','/../config.py']:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request(path)
            self.assertEqual(error.exception.code,404)
    def test_csrf_and_origin(self):
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/sessions',{},app=False)
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/sessions',{},extra={'Origin':'https://evil.example'})
        self.assertEqual(error.exception.code,403)
    def test_token_and_version(self):
        created=self.request('/api/sessions',{'kind':'hub','description':'Implement a basic email validation function.'});s=created['session'];token=created['session_token']
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/next',{'id':s['id'],'version':0},token='wrong')
        updated=self.request('/api/next',{'id':s['id'],'version':0},token)['session'];self.assertEqual(updated['phase'],'planned')
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/next',{'id':s['id'],'version':0},token)
        self.assertEqual(error.exception.code,409)
    def test_local_gate_uses_no_llm(self):
        result=self.request('/api/gate',{'code':BAD});self.assertFalse(result['accepted']);self.assertTrue(result['qa']['pass']);self.assertEqual(self.model.calls,[])

if __name__=='__main__':unittest.main()
