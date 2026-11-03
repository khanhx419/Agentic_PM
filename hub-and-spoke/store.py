import sqlite3,json,secrets,time,hashlib,threading
from pathlib import Path
from contextlib import contextmanager

class Store:
    def __init__(self,folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);self.path=folder/'sessions.sqlite3';self.mutex=threading.Lock();self.locks={}
        with self.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, token_hash TEXT, updated REAL, state TEXT)')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            with db:yield db
        finally:db.close()
    def create(self,state):
        sid=secrets.token_urlsafe(18);token=secrets.token_urlsafe(32);state['id']=sid
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE updated < ?',(time.time()-86400,))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(sid,hashlib.sha256(token.encode()).hexdigest(),time.time(),json.dumps(state,ensure_ascii=False)))
        return state,token
    def get(self,sid,token):
        if not isinstance(sid,str) or not isinstance(token,str):raise ValueError('Phiên không hợp lệ.')
        with self.connect() as db:row=db.execute('SELECT token_hash,updated,state FROM sessions WHERE id=?',(sid,)).fetchone()
        if not row or not secrets.compare_digest(row[0],hashlib.sha256(token.encode()).hexdigest()) or row[1]<time.time()-86400:raise ValueError('Phiên không tồn tại hoặc đã hết hạn.')
        return json.loads(row[2])
    def save(self,state):
        with self.connect() as db:db.execute('UPDATE sessions SET state=?,updated=? WHERE id=?',(json.dumps(state,ensure_ascii=False),time.time(),state['id']))
    def lock(self,sid):
        with self.mutex:
            if sid not in self.locks:self.locks[sid]=threading.Lock()
            return self.locks[sid]
