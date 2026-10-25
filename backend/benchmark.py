"""Read-only benchmark result access; sealed case generation is outside runtime."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def fingerprint():
    paths=sorted((ROOT/'backend').glob('*.py'))+[ROOT/'tests'/'benchmark_independent.py',ROOT/'tests'/'planner_pilot.py']
    digest=hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()


def results():
    path=ROOT/'docs'/'independent-results.json'
    if not path.exists():return dict(status='NOT_RUN')
    report=json.loads(path.read_text(encoding='utf-8'))
    if report['code_hash']!=fingerprint():
        return dict(status='STALE',reason='Candidate code changed; rerun the independent evaluator')
    report['planner_pilot']=planner_pilot()
    return report


def planner_pilot():
    path=ROOT/'docs'/'planner-pilot-results.json'
    if not path.exists():return dict(status='NOT_RUN')
    report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('code_hash')!=fingerprint():
        return dict(status='STALE',reason='Candidate or pilot changed; rerun the pinned-provider pilot')
    return report
