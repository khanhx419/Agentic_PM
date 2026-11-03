import copy
import time
from governance import scan,qa,redact_code
from llm import ModelError

COMMON='The user is demonstrating a small real system. Do not fabricate a test result or say a checker passed. All checks run in separate trusted Python code. Explanations in Vietnamese, JSON keys as specified. '
PROMPTS={
 'planner':COMMON+'''You are Story Planner. Break the request into ONE narrowly scoped story for a Python function validate_email(email) -> bool. Contract: trim surrounding whitespace, accept a simple address with exactly one @, nonempty local part, a domain containing a dot with nonempty labels, no embedded whitespace. Do not implement RFC-perfect email or network checks. Policy: no hardcoded secrets, no I/O, only imports re and os, only os.getenv for configuration. Return {"story":{"title":"...","acceptance":["..."],"scope":"..."}}. State unsupported requests in scope, do not silently broaden the task.''',
 'developer':COMMON+'''You are Developer. Implement exactly one Python function validate_email(email) -> bool, following story and trusted contract. Allowed subset: imports re and os (or from os import getenv), module constants, def with one argument, local assignments, if/elif/else, return, boolean/comparison operations, string strip/lower/split/count/startswith/endswith, len, bool, re.fullmatch/match/search. No loops, helper functions, decorators, comprehensions, exception blocks, eval, exec, filesystem, network or environment printing. Use re.fullmatch(r"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+", email.strip()) is not None for a straightforward supported solution. If secret configuration is needed, use os.getenv("SECRET_KEY") without literal fallback. Do not add secret configuration when unnecessary. Return {"code":"Python source only, no markdown","summary":"..."}. If feedback is present, fix the actual code based on failing tests and AST findings, preserve supported interface. Never return a made-up PASS.''',

}

# Trạng thái chung của phiên: mỗi lần bấm chuyển đúng một bước.
def initial(kind,description,initial_code=''):
    if kind != 'hub':raise ValueError('Bản demo này chỉ hỗ trợ Hub-and-Spoke.')
    if not isinstance(description,str) or not 20<=len(description)<=10000:raise ValueError('Yêu cầu cần từ 20 đến 10.000 ký tự.')
    if not isinstance(initial_code,str) or len(initial_code)>12000:raise ValueError('Mã đầu vào quá dài.')
    return {'kind':kind,'description':description,'initial_code':initial_code,'phase':'ready','status':'ready',
            'story':None,'code':'','revision':0,'qa':None,'governance':None,'seeker':None,'weaver':None,'verified':None,
            'result':None,'validation':None,'schedule_attempts':0,'repairs':0,'events':[],'calls':[],'last_error':None,
            'created_at':time.time(),'version':0}

def event(s,actor,message):s['events'].append({'actor':actor,'message':message,'time':time.time()})

# Mỗi vai trò dùng prompt riêng nhưng có thể gọi chung một model Gemini.
def call(s,model,role,payload):
    data,meta=model.call(role,PROMPTS[role],payload)
    s['calls'].append(meta)
    if not isinstance(data,dict):raise ModelError('Kết quả agent không phải JSON object.')
    return data

def get_code(data):
    code=data.get('code')
    if not isinstance(code,str) or not 1<=len(code)<=12000:raise ModelError('Developer không trả mã Python hợp lệ trong trường code.')
    if code.strip().startswith('```'):raise ModelError('Developer trả markdown thay vì mã nguồn. Thử lại bước này.')
    return code

# PASS cần cả QA và Governance; không tin lời model tự nhận đã đạt.
def check_hub(s):
    s['governance']=scan(s['code'])
    # Interpreter is not host exec, even when Governance already found a secret.
    s['qa']=qa(s['code'])
    passed=s['governance']['pass'] and s['qa']['pass']
    s['phase']='review' if passed else 'blocked'
    s['status']='review' if passed else 'blocked'
    event(s,'QA → Coordinator','PASS' if s['qa']['pass'] else 'FAIL: chức năng chưa đạt hoặc vượt phạm vi kiểm thử.')
    event(s,'Governance → Coordinator','PASS: đạt các quy tắc AST hiện tại.' if s['governance']['pass'] else 'FAIL: mã vi phạm quy tắc AST.')

# Coordinator: chọn vai trò theo trạng thái; confirmed là xác nhận người dùng.
def advance(state,model,confirmed=False):
    s=copy.deepcopy(state)
    if s['status'] in ('accepted','complete','exhausted','clarification'):raise ValueError('Phiên đã dừng. Tạo phiên mới để đổi yêu cầu.')
    if s['kind']=='hub':
        if s['phase']=='ready':
            data=call(s,model,'planner',{'request':s['description']})
            story=data.get('story')
            if not isinstance(story,dict) or not isinstance(story.get('title'),str) or not isinstance(story.get('acceptance'),list):raise ModelError('Planner cần trả title và acceptance trong story.')
            s['story']=story;s['phase']='planned';s['status']='running';event(s,'Planner → Coordinator','Đã tạo story và tiêu chí chấp nhận bằng Gemini.')
        elif s['phase']=='planned':
            if s['initial_code'].strip():
                s['code']=s['initial_code'];event(s,'Người dùng → Coordinator','Tiếp nhận mã có sẵn; bước này không gọi LLM để tạo mã.')
            else:
                s['code']=get_code(call(s,model,'developer',{'request':s['description'],'story':s['story']}));event(s,'Developer → Coordinator','Gemini đã tạo bản mã r1.')
            s['revision']=1;s['phase']='coded'
        elif s['phase']=='coded':check_hub(s)
        elif s['phase']=='blocked':
            if s['repairs']>=3:s['status']='exhausted';event(s,'Coordinator','Dừng sau 3 lần sửa; mã chưa được chấp nhận.')
            else:
                feedback={'qa':s['qa'],'governance':s['governance']}
                s['code']=get_code(call(s,model,'developer',{'request':s['description'],'story':s['story'],'code_to_repair':redact_code(s['code']),'trusted_feedback':feedback}))
                s['repairs']+=1;s['revision']+=1;s['qa']=None;s['governance']=None;s['phase']='coded';s['status']='running'
                event(s,'Developer → Coordinator',f'Gemini đã sửa mã r{s["revision"]}; phải kiểm tra lại.')
        elif s['phase']=='review':
            if not confirmed:raise ValueError('Cần xác nhận xem xét trước khi chấp nhận mã.')
            s['phase']='accepted';s['status']='accepted';event(s,'Người dùng → Coordinator','Chấp nhận kết quả đã qua kiểm tra. Không merge hay triển khai tự động.')
        else:raise ValueError('Trạng thái Hub không hợp lệ.')
    s['last_error']=None;s['version']+=1
    return s
