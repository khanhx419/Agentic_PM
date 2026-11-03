"""Interactive local key setup; never paste keys into chat or a browser form."""
from pathlib import Path
from getpass import getpass
import re

def main():
    print('Lay key tai https://aistudio.google.com/apikey (Free Tier project).')
    print('Key chi luu trong .env tren may. Khong upload file nay len GitHub.')
    key=getpass('Gemini API key (an khi nhap): ').strip()
    if not key or '\n' in key or '\r' in key:raise SystemExit('Key rong/khong hop le, chua ghi file.')
    model=input('Model [gemini-3.5-flash-lite]: ').strip() or 'gemini-3.5-flash-lite'
    if not re.fullmatch(r'[a-zA-Z0-9._-]{1,100}',model):raise SystemExit('Ten model khong hop le.')
    path=Path(__file__).with_name('.env')
    path.write_text('GEMINI_API_KEY='+key+'\nGEMINI_MODEL='+model+'\nGEMINI_MAX_OUTPUT_TOKENS=4096\nGEMINI_TIMEOUT_SECONDS=100\n',encoding='utf-8')
    print('Da luu .env. Chay start.cmd hoac python app.py; giao dien se doc cau hinh moi.')

if __name__=='__main__':main()
