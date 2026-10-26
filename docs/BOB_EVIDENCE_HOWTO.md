# Capturing IBM Bob evidence

AC-12 and Bob-A1 to Bob-A3 are worth 10 of the 25 marks — the same weight as the entire
application demonstration. The repository currently holds **no** Bob evidence, so that
category is at zero regardless of how well the app works.

`scripts/bob_log.py` makes capturing it mechanical. It records what happened; it cannot
invent anything, and it refuses to mark an entry presentable until a real prompt, a real
diff, real test output and a named human reviewer all exist.

## Once, before you start

```powershell
python scripts\bob_log.py baseline
```

Records the current commit as the pre-event baseline. Work at or before it predates the
event and is not attributable to Bob. **This is Bob-A3** — the rule that no pre-existing
code is passed off as Bob's. Drawing that line yourself reads far better to a judge than
leaving it blurred.

## For each Bob session

**1. Open the entry *before* you talk to Bob.** Recording the objective before you know the
outcome is what makes it evidence rather than a reconstruction.

```powershell
python scripts\bob_log.py new --member "Ash" --mode agent `
  --objective "Add independent meter-inventory validation before loss classification" `
  --requirement "AC-13" --version "<installed Bob version>"
```

It prints an entry id (E001, E002…) and creates two files.

**2. Work with Bob.** Paste the exact prompt into `docs/bob-evidence/prompts/eNNN-prompt.md`
and what Bob returned into `docs/bob-evidence/responses/eNNN-response.md`. Paste them
verbatim, including anything you rejected — a judge who sees only polished prompts assumes
curation.

**3. Review it as a human, then commit.** Someone other than the feature owner should review
anything high-risk.

**4. Run the tests and save the output to a file.**

```powershell
.\.venv\Scripts\python.exe -m pytest -q > artifacts\e001-pytest.txt 2>&1
```

**5. Close the entry.**

```powershell
python scripts\bob_log.py close E001 --test "pytest -q" --output "artifacts\e001-pytest.txt" `
  --reviewer "Saish" --result "89 passed" `
  --accepted "inventory check and regression test" `
  --rejected "suggested caching, which would have hidden the defect" `
  --limitation "synthetic fixtures only; no field validation"
```

## Before the demo

```powershell
python scripts\bob_log.py check    # non-zero exit if anything is not presentable
python scripts\bob_log.py index    # regenerates docs/bob-evidence/README.md
```

`check` fails an entry that is still open, missing a prompt, diff, test output or reviewer,
or whose prompt file is still the generated placeholder. If it passes, every entry in the
index is backed by real artifacts.

## What to actually do with Bob

PRD §19 already picks the strongest story, and it is worth following:

> A naive missing-meter case produces an incorrect alert. Bob assists with independent
> expected-inventory validation and a regression test. The same scenario then produces a
> data-quality action, while a complete persistent-loss scenario still triggers inspection.

One genuine bug repair — failing test, fix, passing test — beats five polished prompts.
If that particular defect never occurs, substitute a real one and describe it accurately.
Do not manufacture a defect.

Good candidates in this codebase right now:

- `/api/assets/{aid}/history` exists and has no UI. A small, self-contained feature.
- The ranking engine's action catalogue could use a Bob-written review of whether the
  authored likelihoods are internally consistent (Ask mode, no code change).
- Scenario G currently converges on the same first check for three of four variants. A
  genuine open problem, and a Bob session reasoning about it would be honest evidence.

## Rules the scaffold enforces

| Rule | How |
| --- | --- |
| Bob-A1: material change linked to real Bob work | entry requires a commit and a prompt |
| Bob-A2: human review and reproducible tests | `--reviewer` and `--output` are mandatory |
| Bob-A3: nothing pre-existing attributed to Bob | baseline commit recorded and printed in the index |

## One thing to say out loud in the demo

Bob is the development assistant. It is **not** the runtime theft classifier, not the
planner inside the app, and not a drone pilot. The planner in `backend/investigations.py`
uses Granite at runtime, which is a separate thing from Bob-assisted engineering. Keeping
those apart is the difference between a credible submission and an overclaimed one.
