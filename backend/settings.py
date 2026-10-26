"""Load a local optional .env as data, never as executable shell text."""
import os
from pathlib import Path

ALLOWED={'WATSONX_API_KEY','WATSONX_PROJECT_ID','WATSONX_URL','WATSONX_MODEL_ID',
         'GEMINI_API_KEY','GEMINI_MODEL_ID','LANGSMITH_TRACING'}


def load_environment():
    path=Path(__file__).resolve().parents[1]/'.env'
    if not path.exists():return
    for number,line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'):continue
        if '=' not in line:raise ValueError(f'Invalid .env entry at line {number}')
        key,value=line.split('=',1);key=key.strip();value=value.strip()
        if key not in ALLOWED:continue
        if len(value)>=2 and value[0] in ('"',"'") and value[0]==value[-1]:value=value[1:-1]
        elif len(value)==1 and value[0] in ('"',"'"):value=''
        if value:os.environ.setdefault(key,value)
