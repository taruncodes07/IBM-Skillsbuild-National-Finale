"""External container smoke check; use a disposable Compose project/database.

Seed mode creates one fictional case without making model calls. Verify mode
checks the same case after container restart/recreation. Run with host httpx.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import httpx


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def check(client):
    health=client.get('/api/health');health.raise_for_status()
    page=client.get('/');page.raise_for_status()
    assert 'Grid Trace' in page.text
    for asset in re.findall(r'(?:src|href)="([^"]+)"',page.text):
        if asset.startswith('/assets/'):
            response=client.get(asset);response.raise_for_status();assert response.content
    assert client.get('/grid-trace.svg').status_code==200
    assert client.get('/.env').status_code==404
    assert client.get('/backend/providers.py').status_code==404
    benchmark=client.get('/api/benchmark');benchmark.raise_for_status()
    assert benchmark.json()['adaptive']['status']=='COMPLETED',benchmark.text[:200]


def seed(client):
    created=client.post('/api/runs',json=dict(seed=814,scenario='visible_unmetered_load'))
    created.raise_for_status();rid=created.json()['run']['id']
    for _ in range(3):
        response=client.post(f'/api/runs/{rid}/control',json=dict(command='step'));response.raise_for_status()
    snapshot=client.get(f'/api/runs/{rid}/snapshot').json()
    alert=next(a for a in snapshot['alerts'] if a['boundary_asset_id']=='branch-03')
    with client.stream('GET',f'/api/runs/{rid}/events?after_seq=-1') as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith('event:'):
                assert line=='event: snapshot';break
        else:raise AssertionError('No SSE snapshot event')
    body=dict(alert_id=alert['id'],sequence=3,idempotency_key='container-smoke')
    response=client.post('/api/cases',json=body);response.raise_for_status();case=response.json()
    assert client.post('/api/cases',json=body).json()['id']==case['id']
    for state,actor in [('triaged','analyst'),('under_review','reviewer'),('field_check_required','reviewer')]:
        response=client.patch('/api/cases/'+case['id'],headers={'x-actor':actor},
            json=dict(expected_revision=case['revision'],state=state,reason='Docker smoke check; fictional data; cause unconfirmed.'))
        response.raise_for_status();case=response.json()
    export=client.get('/api/cases/'+case['id']+'/export');export.raise_for_status()
    assert hashlib.sha256(export.content).hexdigest()==export.headers['X-Content-SHA256']
    report=export.json()
    return dict(run_id=rid,case_id=case['id'],analysis_hash=digest(report['analysis']),revision=case['revision'])


def verify(client,state):
    response=client.get('/api/cases/'+state['case_id']+'/export');response.raise_for_status();report=response.json()
    assert report['case']['state']=='field_check_required'
    assert report['case']['revision']==state['revision']
    assert report['case']['analysis_sequence']==3
    assert digest(report['analysis'])==state['analysis_hash']
    assert len(report['audit'])==4 and not report['missions']
    assert report['case']['id'] in client.get('/api/cases/'+state['case_id']+'/export?format=md').text


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--mode',choices=['seed','verify'],required=True)
    parser.add_argument('--state',type=Path,required=True)
    args=parser.parse_args()
    with httpx.Client(base_url=args.url,timeout=20) as client:
        check(client)
        if args.mode=='seed':
            state=seed(client);args.state.parent.mkdir(parents=True,exist_ok=True)
            args.state.write_text(json.dumps(state,indent=2),encoding='utf-8')
        else:state=json.loads(args.state.read_text(encoding='utf-8'))
        verify(client,state)
    print(json.dumps(dict(status='PASS',mode=args.mode,case_id=state['case_id'],checks=['frontend assets','API health','saved evaluation','SSE','role review','exports','frozen analysis','persistent case'])))
