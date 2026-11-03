"""A deliberately small Python AST interpreter. Never eval/exec generated code."""
import ast,json,sys,re,operator

class Returned(Exception):
    def __init__(self,value):self.value=value

# Bộ thông dịch tập con AST; không chạy mã sinh bằng exec/eval.
class Interpreter:
    def __init__(self,code):
        self.tree=ast.parse(code);self.functions=[n for n in self.tree.body if isinstance(n,ast.FunctionDef)]
        if len(self.functions)!=1 or self.functions[0].name!='validate_email':raise ValueError('Cần hàm validate_email(email).')
        self.ticks=0;self.globals={}
        for node in self.tree.body:
            if isinstance(node,ast.Import):
                for item in node.names:
                    if item.name not in ('re','os'):raise ValueError('Import không hỗ trợ.')
                    self.globals[item.asname or item.name]=('module',item.name)
            elif isinstance(node,ast.ImportFrom):
                for item in node.names:
                    if node.module not in ('re','os'):raise ValueError('Import không hỗ trợ.')
                    self.globals[item.asname or item.name]=('function',node.module,item.name)
            elif isinstance(node,(ast.Assign,ast.AnnAssign)):self.statement(node,self.globals)
            elif not isinstance(node,ast.FunctionDef) and not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)):raise ValueError('Lệnh module không hỗ trợ.')
    def budget(self):
        self.ticks+=1
        if self.ticks>4000:raise ValueError('Quá giới hạn thao tác.')
    def expression(self,node,env):
        self.budget()
        if isinstance(node,ast.Constant):return node.value
        if isinstance(node,ast.Name):
            if node.id in env:return env[node.id]
            if node.id in self.globals:return self.globals[node.id]
            raise ValueError('Biến không xác định: '+node.id)
        if isinstance(node,ast.BoolOp):
            result=None
            for value in node.values:
                result=self.expression(value,env)
                if isinstance(node.op,ast.And) and not result:return result
                if isinstance(node.op,ast.Or) and result:return result
            return result
        if isinstance(node,ast.UnaryOp):
            value=self.expression(node.operand,env)
            if isinstance(node.op,ast.Not):return not value
            if isinstance(node.op,ast.USub) and type(value) in (int,float):return -value
            raise ValueError('Toán tử không hỗ trợ.')
        if isinstance(node,ast.Compare):
            left=self.expression(node.left,env)
            ops={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.Is:operator.is_,ast.IsNot:operator.is_not,ast.In:lambda a,b:a in b,ast.NotIn:lambda a,b:a not in b}
            for op,comp in zip(node.ops,node.comparators):
                right=self.expression(comp,env)
                if type(op) not in ops or not ops[type(op)](left,right):return False
                left=right
            return True
        if isinstance(node,ast.IfExp):return self.expression(node.body if self.expression(node.test,env) else node.orelse,env)
        if isinstance(node,(ast.List,ast.Tuple)):
            if len(node.elts)>100:raise ValueError('Danh sách quá dài.')
            return [self.expression(e,env) for e in node.elts]
        if isinstance(node,ast.Subscript):
            value=self.expression(node.value,env);index=self.expression(node.slice,env)
            if not isinstance(value,(str,list,tuple)) or type(index) is not int:raise ValueError('Chỉ hỗ trợ chỉ số nguyên trên chuỗi/danh sách.')
            return value[index]
        if isinstance(node,ast.Slice):raise ValueError('Không hỗ trợ slice; dùng strip/split.')
        if isinstance(node,ast.BinOp):
            a,b=self.expression(node.left,env),self.expression(node.right,env)
            if isinstance(node.op,ast.Add) and isinstance(a,str) and isinstance(b,str) and len(a)+len(b)<10000:return a+b
            if type(a) is int and type(b) is int and abs(a)<10000 and abs(b)<10000:
                if isinstance(node.op,ast.Add):return a+b
                if isinstance(node.op,ast.Sub):return a-b
            raise ValueError('Phép tính ngoài phạm vi.')
        if isinstance(node,ast.Call):
            args=[self.expression(a,env) for a in node.args]
            if node.keywords:raise ValueError('Không dùng keyword arguments trong demo.')
            if isinstance(node.func,ast.Name):
                if node.func.id=='len' and len(args)==1 and isinstance(args[0],(str,list,tuple)):return len(args[0])
                if node.func.id=='bool' and len(args)==1:return bool(args[0])
                if node.func.id=='str' and len(args)==1 and isinstance(args[0],(str,int,float,bool)):return str(args[0])
                func=env.get(node.func.id,self.globals.get(node.func.id))
                if isinstance(func,tuple) and func[0]=='function':return self.module_call(func[1],func[2],args)
            if isinstance(node.func,ast.Attribute):
                obj=self.expression(node.func.value,env);method=node.func.attr
                if isinstance(obj,tuple) and obj[0]=='module':return self.module_call(obj[1],method,args)
                if isinstance(obj,str) and method in ('strip','lower','upper','split','count','find','rfind','startswith','endswith','isalnum','isspace'):
                    if any(not isinstance(a,(str,int)) for a in args):raise ValueError('Đối số chuỗi không hợp lệ.')
                    if len(obj)>10000:raise ValueError('Chuỗi quá dài.')
                    return getattr(obj,method)(*args) # method is one of the fixed names above
            raise ValueError('Hàm gọi ngoài tập con hỗ trợ.')
        raise ValueError('Biểu thức ngoài tập con hỗ trợ: '+type(node).__name__)
    def module_call(self,module,name,args):
        if module=='os' and name=='getenv' and 1<=len(args)<=2:return 'EXAMPLE_ENV_VALUE'
        if module=='re' and name in ('match','search','fullmatch') and len(args)==2 and all(isinstance(a,str) for a in args) and len(args[0])<=250 and len(args[1])<=100:
            return getattr(re,name)(*args)
        raise ValueError('Hàm thư viện ngoài phạm vi.')
    def statement(self,node,env):
        self.budget()
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            value=self.expression(node.value,env)
            for target in targets:
                if not isinstance(target,ast.Name):raise ValueError('Chỉ gán biến đơn.')
                env[target.id]=value
        elif isinstance(node,ast.Return):raise Returned(self.expression(node.value,env) if node.value else None)
        elif isinstance(node,ast.If):
            for stmt in node.body if self.expression(node.test,env) else node.orelse:self.statement(stmt,env)
        elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):pass
        else:raise ValueError('Lệnh ngoài tập con hỗ trợ: '+type(node).__name__)
    def call(self,email):
        function=self.functions[0]
        if len(function.args.args)!=1:raise ValueError('Hàm cần một đối số.')
        env={function.args.args[0].arg:email}
        try:
            for node in function.body:self.statement(node,env)
        except Returned as out:return out.value
        return None

def run(code):
    cases=[('sv@example.com',True),('student.name+tag@school.edu.vn',True),('  sv@example.com  ',True),('',False),('   ',False),('invalid-email',False),('sv@',False),('@example.com',False),('sv@example',False),('a b@example.com',False),('a@@example.com',False),('sv@.com',False),('sv@example.',False),('sv@example..com',False)]
    result=[]
    try:
        interpreter=Interpreter(code)
        for value,expected in cases:
            actual=interpreter.call(value)
            result.append({'input':value,'expected':expected,'actual':actual if type(actual) in (bool,int,float,str,type(None)) else str(type(actual).__name__),'pass':type(actual) is bool and actual==expected})
        return {'pass':all(c['pass'] for c in result),'cases':result,'engine':'restricted_ast_interpreter'}
    except Exception as error:return {'pass':False,'cases':result,'error':str(error)[:250],'engine':'restricted_ast_interpreter'}

if __name__=='__main__':
    request=json.loads(sys.stdin.read(40000));print(json.dumps(run(request['code']),ensure_ascii=True))
