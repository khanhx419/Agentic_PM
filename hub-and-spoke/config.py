"""Configuration is read locally; credentials never go to the browser."""
import os
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

ROOT = Path(__file__).resolve().parent

def settings():
    values={}
    path=ROOT/'.env'
    if path.exists():
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line=raw.strip()
            if line and not line.startswith('#') and '=' in line:
                key,value=line.split('=',1)
                values[key.strip()]=value.strip().strip('"\'')
    def get(key,default=''):return os.environ.get(key,values.get(key,default))
    return {'key':get('GEMINI_API_KEY'),'model':get('GEMINI_MODEL','gemini-3.5-flash-lite'),
            'max_output':int(get('GEMINI_MAX_OUTPUT_TOKENS','4096')),
            'timeout':int(get('GEMINI_TIMEOUT_SECONDS','100'))}

def public_settings():
    c=settings()
    try: framework_version=version('langgraph')
    except PackageNotFoundError: framework_version='not installed'
    return {'provider':'Gemini','model':c['model'],'configured':bool(c['key']), 'orchestrator':'LangGraph', 'orchestrator_version':framework_version,
            'setup':'Chạy python setup_api.py trong thư mục hub-and-spoke để lưu key trên máy. Không gửi key vào chat.',
            'free_tier':'Dùng project Free Tier trong AI Studio; chương trình không kiểm tra được gói thanh toán của tài khoản.'}
