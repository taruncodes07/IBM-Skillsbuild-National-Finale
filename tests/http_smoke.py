"""Real localhost HTTP smoke check. Creates a new demonstration run, preserves old runs."""
import json,time,urllib.request
from pathlib import Path
BASE='http://127.0.0.1:8000'
def request(path,body=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as response:return response.status,response.read()
if __name__=='__main__':
    home_status,home=request('/')
    api_status,_=request('/api/bootstrap')
    _,raw=request('/api/runs',dict(seed=42,scenario='visible_unmetered_load'));s=json.loads(raw);rid=s['run']['id']
    for _ in range(3):_,raw=request(f'/api/runs/{rid}/control',dict(command='step'));s=json.loads(raw)
    assert len(s['readings'])==38;assert len(s['alerts'])==1;assert s['alerts'][0]['boundary_asset_id']=='branch-03'
    assert s['alerts'][0]['consecutive_intervals']==3
    with urllib.request.urlopen(BASE+f"/api/runs/{rid}/events?after_seq={s['run']['event_seq']-1}",timeout=5) as response:
        lines=[response.readline().decode().strip() for _ in range(4)]
        assert lines[0].startswith('id: ');assert lines[1]=='event: snapshot'
    report=dict(disclosure='Real HTTP/API smoke only; no browser interactions or rendered captures.',frontend_http_status=home_status,api_http_status=api_status,run_id=rid,seed=42,sequence=s['seq'],measurement_streams=len(s['readings']),alert_boundary=s['alerts'][0]['boundary_asset_id'],alert_persistence=s['alerts'][0]['consecutive_intervals'],sse_first_event=lines,checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    Path('docs/http-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
