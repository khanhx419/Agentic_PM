import time
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
            'story':None,'code':'','revision':0,'qa':None,'governance':None,
            'repairs':0,'events':[],'calls':[],'last_error':None,
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

# Hàm tương thích với API cũ; điều phối thật nằm trong graph LangGraph.
def advance(state, model, confirmed=False):
    from workflow import run_step
    return run_step(state, model, confirmed)
