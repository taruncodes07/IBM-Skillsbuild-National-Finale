#!/usr/bin/env python3
"""IBM Bob engineering evidence log (PRD AC-12, Bob-A1 to Bob-A3).

Records what Bob was actually asked, what it produced, what a human changed, which
tests were run and what the output was. It records; it never invents. An entry with
no prompt, no diff, no test output or no named human reviewer fails validation, so
an unfinished session cannot be presented as evidence.

Usage
  python scripts/bob_log.py new  --member "Ash" --mode plan --objective "Break the PRD into module contracts"
  python scripts/bob_log.py close E003 --test "pytest -q" --output artifacts/e003-pytest.txt --reviewer "Saish"
  python scripts/bob_log.py index
  python scripts/bob_log.py check
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'docs' / 'bob-evidence'
ENTRIES = STORE / 'entries'
INDEX = STORE / 'README.md'
BASELINE = STORE / 'baseline.json'

MODES = ('plan', 'agent', 'ask')
REQUIRED_TO_CLOSE = ('prompt_path', 'response_path', 'commit', 'test_command',
                     'test_output_path', 'human_reviewer')
PLACEHOLDERS = ('Paste the exact prompt given to IBM Bob.',
                'Paste what Bob actually returned.')


def git(*args, default=''):
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                              text=True, timeout=20).stdout.strip() or default
    except Exception:
        return default


def load_all():
    ENTRIES.mkdir(parents=True, exist_ok=True)
    out = []
    for path in sorted(ENTRIES.glob('*.json')):
        try:
            out.append(json.loads(path.read_text(encoding='utf-8')))
        except json.JSONDecodeError as exc:
            print(f'  ! {path.name} is not valid JSON: {exc}', file=sys.stderr)
    return out


def next_id(entries):
    used = [int(e['id'][1:]) for e in entries if e.get('id', '').startswith('E') and e['id'][1:].isdigit()]
    return 'E%03d' % ((max(used) + 1) if used else 1)


def cmd_baseline(args):
    """Record the pre-event commit, so nothing before it can be claimed as Bob's work."""
    STORE.mkdir(parents=True, exist_ok=True)
    commit = args.commit or git('rev-parse', 'HEAD', default='unknown')
    BASELINE.write_text(json.dumps(dict(
        baseline_commit=commit,
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        note=('Work at or before this commit predates the event and is NOT attributable to '
              'IBM Bob. Every evidence entry must reference a diff after it (Bob-A3).')),
        indent=2) + '\n', encoding='utf-8')
    print(f'Baseline recorded: {commit}')


def cmd_new(args):
    entries = load_all()
    entry_id = next_id(entries)
    ENTRIES.mkdir(parents=True, exist_ok=True)
    prompt_path = STORE / 'prompts' / f'{entry_id.lower()}-prompt.md'
    response_path = STORE / 'responses' / f'{entry_id.lower()}-response.md'
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    if not prompt_path.exists():
        prompt_path.write_text(f'# {entry_id} prompt\n\nPaste the exact prompt given to IBM Bob.\n',
                               encoding='utf-8')
    if not response_path.exists():
        response_path.write_text(f'# {entry_id} response\n\nPaste what Bob actually returned.\n',
                                 encoding='utf-8')
    entry = dict(
        id=entry_id,
        opened_at=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        team_member=args.member,
        bob_version=args.version,
        bob_mode=args.mode,
        objective=args.objective,
        prd_requirement=args.requirement,
        prompt_path=str(prompt_path.relative_to(ROOT)).replace('\\', '/'),
        response_path=str(response_path.relative_to(ROOT)).replace('\\', '/'),
        branch=git('rev-parse', '--abbrev-ref', 'HEAD', default=''),
        commit_at_open=git('rev-parse', 'HEAD', default=''),
        commit=None, diff_summary=None,
        accepted=None, rejected=None,
        test_command=None, test_output_path=None, observed_result=None,
        human_reviewer=None, limitation=None,
        predates_event=False, status='open')
    (ENTRIES / f'{entry_id}.json').write_text(json.dumps(entry, indent=2) + '\n', encoding='utf-8')
    print(f'Opened {entry_id} ({args.mode} mode, {args.member})')
    print(f'  1. Paste the prompt into   {entry["prompt_path"]}')
    print(f'  2. Paste the response into {entry["response_path"]}')
    print(f'  3. Commit your work, then: python scripts/bob_log.py close {entry_id} '
          f'--test "pytest -q" --output <file> --reviewer "<name>"')


def cmd_close(args):
    path = ENTRIES / f'{args.entry_id.upper()}.json'
    if not path.exists():
        sys.exit(f'No entry {args.entry_id}. Run "bob_log.py index" to list them.')
    entry = json.loads(path.read_text(encoding='utf-8'))
    entry['commit'] = args.commit or git('rev-parse', 'HEAD', default='')
    entry['diff_summary'] = git('show', '--stat', '--oneline', entry['commit'], default='')[:2000]
    entry['test_command'] = args.test
    entry['test_output_path'] = args.output
    entry['observed_result'] = args.result
    entry['human_reviewer'] = args.reviewer
    entry['accepted'] = args.accepted
    entry['rejected'] = args.rejected
    entry['limitation'] = args.limitation
    entry['closed_at'] = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    entry['status'] = 'closed'
    path.write_text(json.dumps(entry, indent=2) + '\n', encoding='utf-8')
    print(f'Closed {entry["id"]}. Run "python scripts/bob_log.py check" before the demo.')


def problems(entry):
    found = []
    if entry.get('status') != 'closed':
        found.append('still open')
        return found
    for field in REQUIRED_TO_CLOSE:
        if not entry.get(field):
            found.append(f'missing {field}')
    out = entry.get('test_output_path')
    if out and not (ROOT / out).exists():
        found.append(f'test output file not found: {out}')
    for field in ('prompt_path', 'response_path'):
        p = entry.get(field)
        if p and not (ROOT / p).exists():
            found.append(f'{field} not found: {p}')
            continue
        if not p:
            continue
        body = (ROOT / p).read_text(encoding='utf-8')
        # The scaffold writes these sentences; if they survive, nothing real was pasted in.
        if any(stub in body for stub in PLACEHOLDERS):
            found.append(f'{field} is still the generated placeholder: {p}')
        elif len(body.strip().splitlines()) < 2:
            found.append(f'{field} has no content: {p}')
    if entry.get('predates_event'):
        found.append('marked as predating the event; it cannot be attributed to Bob (Bob-A3)')
    return found


def cmd_check(args):
    entries = load_all()
    if not entries:
        sys.exit('No evidence entries yet. Nothing can be claimed for AC-12 or Bob-A1 to A3.')
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))['baseline_commit'] if BASELINE.exists() else None
    if not baseline:
        print('! No baseline commit recorded. Run: python scripts/bob_log.py baseline')
    bad = 0
    for entry in entries:
        issues = problems(entry)
        if issues:
            bad += 1
            print(f'  FAIL {entry.get("id")}: ' + '; '.join(issues))
        else:
            print(f'  ok   {entry["id"]}  {entry["bob_mode"]:<5} {entry["team_member"]:<10} {entry["objective"][:48]}')
    closed = sum(1 for e in entries if e.get('status') == 'closed')
    print(f'\n{closed} closed of {len(entries)}; {bad} with problems.')
    if bad:
        sys.exit(1)


def cmd_index(args):
    entries = load_all()
    baseline = json.loads(BASELINE.read_text(encoding='utf-8')) if BASELINE.exists() else None
    lines = ['# IBM Bob engineering evidence', '',
             'Every entry below records an interaction that actually happened: the prompt given, '
             'what Bob returned, the resulting diff, who reviewed it, and the test output. '
             'Nothing here is reconstructed after the fact.', '']
    if baseline:
        lines += [f'**Pre-event baseline:** `{baseline["baseline_commit"]}`. '
                  'Work at or before that commit predates the event and is not attributable to '
                  'IBM Bob (Bob-A3).', '']
    else:
        lines += ['**No baseline commit recorded.** Run `python scripts/bob_log.py baseline`.', '']
    if not entries:
        lines += ['_No entries yet._', '']
    else:
        lines += ['| ID | Mode | Member | Objective | Requirement | Commit | Tests | Reviewer |',
                  '| --- | --- | --- | --- | --- | --- | --- | --- |']
        for e in entries:
            lines.append('| {id} | {mode} | {member} | {obj} | {req} | {commit} | {test} | {rev} |'.format(
                id=e.get('id', '?'), mode=e.get('bob_mode', '?'), member=e.get('team_member', '?'),
                obj=(e.get('objective') or '')[:60], req=e.get('prd_requirement') or '-',
                commit=(e.get('commit') or '-')[:9],
                test=(e.get('test_command') or '-')[:28],
                rev=e.get('human_reviewer') or '-'))
        lines.append('')
        for e in entries:
            issues = problems(e)
            lines += [f'## {e.get("id")} — {e.get("objective","")}', '',
                      f'- **Mode:** {e.get("bob_mode")} · **Member:** {e.get("team_member")} · '
                      f'**Bob version:** {e.get("bob_version") or "unrecorded"}',
                      f'- **Prompt:** `{e.get("prompt_path") or "-"}`',
                      f'- **Response:** `{e.get("response_path") or "-"}`',
                      f'- **Commit:** `{e.get("commit") or "-"}`',
                      f'- **Test:** `{e.get("test_command") or "-"}` → `{e.get("test_output_path") or "-"}`',
                      f'- **Observed:** {e.get("observed_result") or "-"}',
                      f'- **Human reviewer:** {e.get("human_reviewer") or "-"}',
                      f'- **Accepted:** {e.get("accepted") or "-"}',
                      f'- **Rejected:** {e.get("rejected") or "-"}',
                      f'- **Limitation:** {e.get("limitation") or "-"}', '']
            if issues:
                lines += [f'> **Not presentable yet:** ' + '; '.join(issues), '']
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {INDEX.relative_to(ROOT)} ({len(entries)} entries)')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    b = sub.add_parser('baseline', help='record the pre-event commit (Bob-A3)')
    b.add_argument('--commit')
    b.set_defaults(func=cmd_baseline)

    n = sub.add_parser('new', help='open an entry BEFORE talking to Bob')
    n.add_argument('--member', required=True)
    n.add_argument('--mode', required=True, choices=MODES)
    n.add_argument('--objective', required=True)
    n.add_argument('--requirement', default=None, help='PRD requirement this serves, e.g. AC-14')
    n.add_argument('--version', default=None, help='installed IBM Bob version')
    n.set_defaults(func=cmd_new)

    c = sub.add_parser('close', help='attach the diff, tests and reviewer')
    c.add_argument('entry_id')
    c.add_argument('--commit')
    c.add_argument('--test', required=True)
    c.add_argument('--output', required=True, help='path to the saved terminal output')
    c.add_argument('--reviewer', required=True, help='human who reviewed the change')
    c.add_argument('--result', default=None)
    c.add_argument('--accepted', default=None)
    c.add_argument('--rejected', default=None)
    c.add_argument('--limitation', default=None)
    c.set_defaults(func=cmd_close)

    sub.add_parser('index', help='regenerate docs/bob-evidence/README.md').set_defaults(func=cmd_index)
    sub.add_parser('check', help='fail if any entry is not presentable').set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
