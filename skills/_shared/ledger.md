# Iteration ledger

Every `/ansh` skill logs its phase boundaries so I can see how many rounds each task takes and
which phases never change the outcome. `/ansh-retro` reads it.

## Logging

Call the script at the end of each phase. It appends one JSON line to
`~/.agentic-workflow/ansh/events.jsonl` (override with `ANSH_LEDGER`).

```bash
"<skills-root>/_shared/ansh-log" <skill> <phase> <verdict> \
  [--goal G] [--task T3] [--milestone M2] [--attempt 2] [--reason missed-edge-case] \
  [--class repo-in-facade] [--surface ui] [--ids AC-3,FM-2] [--pr 19470] [--model gpt-6.1-sol] [--note "..."]
```

Resolve `<skills-root>` from the skill's base directory (follow symlinks). The script fills in
time, repo, branch, head SHA and cwd. A failed log write never fails the skill: note it and go on.

## Fields

- `verdict`: `PASS`, `REVISE`, `DEBUG`, `NEEDS_REPLAN`, `BLOCKED`, `DONE`, `parked`,
  `agent-default`, `merged`, `escaped` (a human or post-merge bug found what verification passed).
- `reason` (pick one): `weak-verification`, `missed-edge-case`, `plan-gap`, `wrong-surface`,
  `regression`, `perf`, `lint`, `types`, `ci-flake`, `ci-stale-base`, `review-comment`,
  `human-correction`, `tooling`, `scope`, `other`.
- `merged` and `escaped` events carry `--goal`, `--milestone` and `--surface` so retro can split
  escape rates by surface. `--surface` takes the four values in
  [verification](verification.md#surface); older `visible` and `invisible` lines read as `ui` and
  `backend`.
- `class` (optional): a short kebab-case name for the specific mistake, e.g. `repo-in-facade` or
  `missing-tenant-filter`. Reuse an existing name when it's the same mistake. `/ansh-correct` groups
  on it, so a class seen twice gets fixed.

## Where to log

| Skill | Log at |
|---|---|
| `/ansh-small-loop`, `/ansh-loop` | tier picked, each wave, final status |
| `/ansh-plan` | plan written, challenge done (one event per agent default) |
| `/ansh-cycle` | each round's verdict (attempt n, reason), BLOCKED at the budget |
| `/ansh-task` | red check written, done (attempt n) |
| `/ansh-review` | verdict per task, per PR gate, whole-goal verdict; `bot-preflight-miss` per bot blocker the pre-flight didn't predict |
| `/ansh-ship` | each PR opened or updated |
| `/ansh-debug` | root cause confirmed, fix verified |
| `/ansh-resolve` | each fix (with reason), dismissal, retry |
| `/ansh-pr-loop` | merged, parked |
| `/ansh-verify` | each run (surface, pass or fail) |
| `/ansh-control`, `/ansh-backend` | each drive or check (surface, pass, fail or blocked) |
| `/ansh-correct` | class fixed (PR opened), class deferred |
| `/ansh-retro` | report written (proposal count) |
| `/ansh-think`, `/ansh-save` | done |
| any | `escaped` when I correct something verification passed |
| any that saves memory | `memory DONE` with the memory or candidate id ([memory](memory.md)) |
