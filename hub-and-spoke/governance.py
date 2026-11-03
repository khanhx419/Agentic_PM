"""AST rules; no generated Python is executed on the host."""
import ast
import re
import json
import subprocess
import sys
from pathlib import Path

SENSITIVE=re.compile(r'secret|token|api_?key|password|passwd|credential',re.I)
BLOCKED={'eval','exec','compile','open','__import__','getattr','setattr','globals','locals','vars','input','breakpoint'}

def literal(node,constants,depth=0):
    if depth>8:return None
    if isinstance(node,ast.Constant):return node.value
    if isinstance(node,ast.Name):return constants.get(node.id)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        a,b=literal(node.left,constants,depth+1),literal(node.right,constants,depth+1)
        if isinstance(a,str) and isinstance(b,str) and len(a)+len(b)<20000:return a+b
    if isinstance(node,ast.JoinedStr):
        parts=[literal(v,constants,depth+1) for v in node.values]
        if all(isinstance(v,str) for v in parts):return ''.join(parts)
    return None

# Duyệt AST và áp quy tắc; không thực thi mã, không bắt mọi loại secret.
def scan(code):
    findings=[]
    def add(rule,node,message):findings.append({'rule':rule,'line':getattr(node,'lineno',1),'message':message})
    if not isinstance(code,str) or not 1<=len(code)<=12000:return {'pass':False,'findings':[{'rule':'SIZE','line':1,'message':'Mã phải có 1–12.000 ký tự.'}]}
    try:tree=ast.parse(code)
    except (SyntaxError,ValueError,RecursionError) as error:return {'pass':False,'findings':[{'rule':'SYNTAX','line':getattr(error,'lineno',1),'message':'Không phân tích được cú pháp Python.'}]}
    nodes=list(ast.walk(tree))
    if len(nodes)>1500:return {'pass':False,'findings':[{'rule':'SIZE','line':1,'message':'Cấu trúc mã quá lớn.'}]}
    constants={}
    for node in nodes:
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            value=literal(node.value,constants)
            for target in targets:
                if isinstance(target,ast.Name):
                    if value is not None:constants[target.id]=value
                    if SENSITIVE.search(target.id) and isinstance(value,str) and value.strip():add('HARDCODED_SECRET',node,'Biến nhạy cảm được gán chuỗi cố định; dùng os.getenv, không đặt giá trị bí mật mặc định.')
        if isinstance(node,ast.Dict):
            for key,value in zip(node.keys,node.values):
                k=literal(key,constants) if key else None;v=literal(value,constants)
                if isinstance(k,str) and SENSITIVE.search(k) and isinstance(v,str) and v.strip():add('HARDCODED_SECRET',node,'Trường nhạy cảm trong dictionary có giá trị viết cứng.')
        if isinstance(node,ast.Call):
            name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
            if name in BLOCKED:add('UNSAFE_CALL',node,'Không cho phép gọi hàm thực thi mã, I/O hoặc truy cập động: '+name)
            if name=='getenv' and len(node.args)>1 and literal(node.args[1],constants):add('SECRET_FALLBACK',node,'Không dùng secret mặc định viết cứng trong getenv.')
        if isinstance(node,ast.Import):
            for alias in node.names:
                if alias.name not in ('re','os'):add('IMPORT',node,'Chỉ hỗ trợ import re và os trong phạm vi demo.')
        if isinstance(node,ast.ImportFrom) and (node.module not in ('re','os') or node.level):add('IMPORT',node,'Import ngoài phạm vi được hỗ trợ.')
        if isinstance(node,ast.ImportFrom) and node.module=='os' and any(a.name!='getenv' for a in node.names):add('IMPORT',node,'Chỉ cho phép from os import getenv.')
        if isinstance(node,(ast.For,ast.While,ast.With,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda,ast.Try,ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp,ast.Await,ast.Global,ast.Nonlocal)):
            add('UNSUPPORTED',node,'Cấu trúc ngoài tập con Python của demo: '+type(node).__name__)
        if isinstance(node,ast.Attribute) and node.attr.startswith('_'):add('ATTRIBUTE',node,'Không cho phép truy cập thuộc tính nội bộ.')
        if isinstance(node,ast.FunctionDef) and (node.decorator_list or node.args.defaults or node.args.kw_defaults):add('FUNCTION',node,'Không dùng decorator hoặc giá trị đối số mặc định.')
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    if len(functions)!=1 or functions[0].name!='validate_email':add('INTERFACE',tree,'Cần đúng một hàm validate_email(email).')
    elif len(functions[0].args.args)!=1 or functions[0].args.vararg or functions[0].args.kwarg or functions[0].args.posonlyargs or functions[0].args.kwonlyargs:add('INTERFACE',functions[0],'Hàm chỉ nhận một đối số email.')
    for node in tree.body:
        if not isinstance(node,(ast.FunctionDef,ast.Import,ast.ImportFrom,ast.Assign,ast.AnnAssign)) and not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)):
            add('TOP_LEVEL',node,'Không đặt lệnh chạy hoặc biểu thức ở mức module.')
    return {'pass':not findings,'findings':findings[:60]}

# Che giá trị secret phát hiện được trước khi gửi mã đi sửa.
def redact_code(code):
    """Mask values flagged as secrets before asking the model to repair user code."""
    result=scan(code);lines=code.splitlines()
    for f in result['findings']:
        if f['rule'] in ('HARDCODED_SECRET','SECRET_FALLBACK') and 0<f['line']<=len(lines):
            line=lines[f['line']-1]
            lines[f['line']-1]=re.sub(r'(["\'])(?:\\.|(?!\1).)*?\1',lambda m:m.group(1)+'REDACTED'+m.group(1),line)
    return '\n'.join(lines)

# Chạy worker thông dịch AST giới hạn để kiểm tra chức năng, không exec mã sinh.
def qa(code):
    """Run a restricted AST interpreter in a separate bounded worker, never exec()."""
    try:
        p=subprocess.run([sys.executable,'-X','utf8','-I',str(Path(__file__).with_name('qa_worker.py'))],input=json.dumps({'code':code}),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=4)
        if p.returncode:return {'pass':False,'cases':[],'error':'Bộ kiểm tra không xử lý được tập con mã này; yêu cầu Developer viết lại theo giao diện hỗ trợ.'}
        return json.loads(p.stdout)
    except subprocess.TimeoutExpired:return {'pass':False,'cases':[],'error':'Kiểm thử vượt 4 giây; mã không được chấp nhận.'}
    except (ValueError,OSError):return {'pass':False,'cases':[],'error':'Không khởi chạy được bộ kiểm tra.'}
