import sqlite3,json,os,uuid
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(os.environ.get('GRIDTRACE_DATA',Path(__file__).resolve().parents[1]/'data'))
ROOT.mkdir(parents=True,exist_ok=True)
(ROOT/'evidence').mkdir(exist_ok=True)
DB=sqlite3.connect(ROOT/'gridtrace.sqlite3',check_same_thread=False)
DB.execute('PRAGMA journal_mode=WAL'); DB.execute('PRAGMA foreign_keys=ON')
DB.executescript('''CREATE TABLE IF NOT EXISTS objects(kind TEXT NOT NULL,id TEXT PRIMARY KEY,body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS intervals(run_id TEXT,seq INTEGER,body TEXT NOT NULL,PRIMARY KEY(run_id,seq));
CREATE TABLE IF NOT EXISTS private_truth(run_id TEXT,seq INTEGER,body TEXT NOT NULL,PRIMARY KEY(run_id,seq));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,case_id TEXT,body TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;''')

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def uid(prefix): return prefix+'-'+uuid.uuid4().hex[:12]
def put(kind,obj):
    DB.execute('INSERT INTO objects VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(kind,obj['id'],json.dumps(obj,allow_nan=False))); DB.commit(); return obj
def get(id):
    r=DB.execute('SELECT body FROM objects WHERE id=?',(id,)).fetchone()
    return json.loads(r[0]) if r else None
def all_of(kind): return [json.loads(r[0]) for r in DB.execute('SELECT body FROM objects WHERE kind=? ORDER BY rowid DESC',(kind,))]
def interval(run_id,seq):
    r=DB.execute('SELECT body FROM intervals WHERE run_id=? AND seq=?',(run_id,seq)).fetchone()
    return json.loads(r[0]) if r else None
def save_interval(run_id,seq,body,truth):
    DB.execute('INSERT INTO intervals VALUES(?,?,?)',(run_id,seq,json.dumps(body,allow_nan=False)))
    DB.execute('INSERT INTO private_truth VALUES(?,?,?)',(run_id,seq,json.dumps(truth,allow_nan=False))); DB.commit()
def audit(case,actor,action,old,reason='',refs=None):
    from .simulation import stamp
    run=get(case['run_id'])
    event=dict(case_id=case['id'],actor_id=actor,actor_role=actor,action=action,from_state=old,to_state=case['state'],reason=reason,wall_timestamp=now(),simulation_timestamp=stamp(run['seq']+1),object_revision=case['revision'],references=refs or [])
    c=DB.execute('INSERT INTO audit(case_id,body) VALUES(?,?)',(case['id'],json.dumps(event))); DB.commit(); return c.lastrowid
def audits(case_id): return [dict(id=r[0],**json.loads(r[1])) for r in DB.execute('SELECT id,body FROM audit WHERE case_id=? ORDER BY id',(case_id,))]
