"""Read-only benchmark result access; sealed case generation is outside runtime."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def fingerprint():
    paths=sorted((ROOT/'backend').glob('*.py'))+[ROOT/'tests'/name for name in ('benchmark_independent.py','planner_pilot.py','adaptive_evaluation.py')]
    digest=hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()


def results():
    path=ROOT/'docs'/'independent-results.json'
    report=json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(status='NOT_RUN')
    if report.get('code_hash')!=fingerprint() and path.exists():
        report=dict(status='STALE',reason='Candidate code changed; rerun the independent evaluator')
    report['planner_pilot']=planner_pilot()
    report['adaptive']=adaptive()
    return report


def planner_pilot():
    path=ROOT/'docs'/'planner-pilot-results.json'
    if not path.exists():return dict(status='NOT_RUN')
    report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('code_hash')!=fingerprint():
        return dict(status='STALE',reason='Candidate or pilot changed; rerun the pinned-provider pilot')
    return report


def adaptive():
    path=ROOT/'docs'/'adaptive-results.json'
    if not path.exists():return dict(status='NOT_RUN')
    report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('code_hash')!=fingerprint():
        return dict(status='STALE',reason='Candidate or evaluator changed; rerun the full adaptive evaluation')
    # Complete trace artifacts stay in the downloadable report, keeping API polling small.
    return {**report,'cases':[{k:v for k,v in row.items() if k not in ('trace','checks','planner_history','provider_attempts')} for row in report['cases']]}
