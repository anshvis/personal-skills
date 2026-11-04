---
name: ansh-pr-loop
description: "Drive one PR to merged: run the /ansh-review pr gate, hand its findings to /ansh-resolve, repeat /ansh-resolve on a ~5 minute cadence until CI is green and no review blocks, then merge per autonomy.md's merge rule; use for /ansh-pr-loop <n>, \"babysit this PR\", or when /ansh-ship opens a PR."
---

# /ansh-pr-loop

**Goal:** an open PR becomes merged, parked or awaiting approval, with evidence on its head SHA.

**Uses:** [memory](../_shared/memory.md), [`/ansh-review`](../ansh-review/SKILL.md) (`pr` mode), [`/ansh-resolve`](../ansh-resolve/SKILL.md),
[`/ansh-verify`](../ansh-verify/SKILL.md), [`/ansh-plan`](../ansh-plan/SKILL.md),
[autonomy](../_shared/autonomy.md), [verification](../_shared/verification.md),
[stacking](../_shared/stacking.md), [worktrees](../_shared/worktrees.md),
[runtime](../_shared/runtime.md), [ledger](../_shared/ledger.md) with `_shared/ansh-log`,
[outcomes](references/outcomes.md), [comment templates](references/comments.md),
[CI triage](../ansh-resolve/references/ci-triage.md), [GitHub recipes](../ansh-resolve/references/github.md).

Arguments: `/ansh-pr-loop [<n>] [via=ansh-loop|ansh-small-loop] [reviewed]`, or
`/ansh-pr-loop stats` ([outcomes](references/outcomes.md)). Wakeups pass `reviewed` to skip step 3
when the head hasn't moved.

## Steps

1. **Identify the PR once.** Take `<n>`, or resolve it from the current branch
   (`gh pr view --json number,url,headRefName`). Name it in the first status line. Work in the
   worktree that tracks its branch ([worktrees](../_shared/worktrees.md)). Check ownership: PR
   author against `gh api user -q .login`. Not mine: read-only from here on. Run
   `/ansh-review pr <n>` and report. No pushes, comments, fixes or merges (autonomy).
2. **Pin the head.** `git fetch origin`. If `git merge-base --is-ancestor origin/<base> HEAD`
   fails, merge the base in and push per [stacking](../_shared/stacking.md). Record the head SHA.
3. **Review gate.** Run `/ansh-review pr <n>` at the pinned SHA. It reuses or reruns its lenses,
   posts the gate and merge-call comments, and returns `VERDICT`, `MERGE_LANE`, `PARKED`,
   `WAITING_ON` and the gate rows. Keep them in the state file.
4. **Fix the gate's findings.** Hand the rows the gate marks for fixing to `/ansh-resolve <n>` as
   items, the `bot-preflight` rows included. A `human-approval-required` row means the bot will
   never approve this PR, so request a CODEOWNERS or human reviewer now instead of at merge time. Then run `/ansh-review pr <n>` again with resolve's report: it does the head bookkeeping
   and judges the fixed head, so its lane and park call reflect the fixed code.
5. **Iterate.** Each iteration:
   1. Run one `/ansh-resolve` pass on the PR. It owns CI triage, comment triage, fixes, replies,
      thread resolution and fix logging. **Pre-flight before every push of our own commits:** run
      `/ansh-review pr <n> preflight` on the local head and fix its `likely` rows first, so the
      bot reviews code that already passes what it checks. A merge of the base alone skips it.
   2. **vitalize-agent gate.** Find `vitalize-agent[bot]`'s review whose `commit_id` equals
      `headRefOid`. None yet: not converged; arm a one-off recheck 30 minutes after the push
      (`ScheduleWakeup` 1800s, or T3 `schedule_task` on this thread) on top of the watcher. It
      left findings: `/ansh-resolve` fixes them like any review. For each blocking finding the
      pre-flight didn't predict for that head, log a `bot-preflight-miss`
      ([bot pre-flight](../ansh-review/references/bot-preflight.md#learning-from-misses)). It raised
      a finding we already answered: post the pre-emptive reply from the gate row and resolve the
      thread. It approved the head with no open findings: passed.
   3. **Stuck bot reviews.** For each bot review at `CHANGES_REQUESTED` whose findings all have a
      verified disposition, count consecutive iterations it stays stuck after the fix was pushed.
      At two, dismiss it ([GitHub recipes](../ansh-resolve/references/github.md)) and post the
      dismissal comment ([templates](references/comments.md)). Any doubt counts as not yet.
   4. **Dependencies.** For each `WAITING_ON` PR, post or edit the `waiting-on` comment and watch
      that PR too. When one merges, retarget, merge the new base, re-verify and push per
      [stacking](../_shared/stacking.md), then edit the comment.
   5. **Head moved** (a fix, a base merge, a retarget): run `/ansh-review pr <n>` at the new head
      for a fresh `VERDICT`, `MERGE_LANE` and `PARKED`.
   6. Post a short status: CI per check (CI triage format), reviews, what changed, what blocks.
6. **Parked short-circuit.** `/ansh-review` says `PARKED: yes`, or `/ansh-resolve` returns PARKED:
   finish every check that doesn't need the forbidden action, then go straight to the parked branch
   of step 8. Don't wait for a green that needs the parked step.
   **Converged when all hold on the head SHA:** every required check's build for this SHA passed;
   no review at `CHANGES_REQUESTED`; `/ansh-resolve` returned DONE with every comment traced;
   vitalize-agent passed this SHA; every gate blocker and major is fixed or dismissed with
   evidence verified by the appropriate lens; the thermo-nuclear lens meets its approval bar;
   no new major-or-worse finding since the gate; `/ansh-review` says `VERDICT: PASS` and
   `LOOP_CLOSURE: closed`. An agent default alone cannot waive a verification or quality finding.
7. **Prove the head.** Run `/ansh-verify run` for the PR's packets at this exact SHA. Its
   `manifest.json` must list every check in every packet this PR covers, each passing
   ([verification](../_shared/verification.md#evidence-pack)). Any new commit, including a base
   merge, needs it again. Apply [closing the loop](../_shared/verification.md#closing-the-loop):
   a passing manifest must cover the intended behavior and affected callers, not just the checks
   the author happened to list. Missing coverage returns to verification and review before step 8.
   `/ansh-verify` posts the evidence comment.
8. **Merge decision**, first match wins. Cornerstone, foundational and `ansh-correct` PRs use
   these same gates; their names and labels add no approval hold.
   - Not our PR: never merge, never post. Report the gate findings. Outcome `needs_review`.
   - `PARKED: yes`, or merging would do anything on autonomy's never-do list: post the parked
     comment with the exact command or click, log `parked`, stop. Outcome `parked`.
   - `WAITING_ON` not empty: hold. Keep watching. Merge only after every dependency merged and
     the base is current ([stacking](../_shared/stacking.md)).
   - `LOOP_CLOSURE` missing or open, or `QUALITY` missing or not pass: return to steps 3–7
     to strengthen verification or resolve quality findings. Older gate reports need review
     again. Unavailable required capabilities return BLOCKED with the missing piece. Neither
     merge nor arm auto-merge until both gates pass at the head SHA.
   - `MERGE_LANE: deep`: run `/ansh-review pr <n>` in the deep lane at the head SHA in a fresh
     subagent; it does the fresh-context review and re-runs the verification itself. Its
     `DEEP_LANE` line must read `done` and `pass`. On pass, record `deep_lane_sha` in the state
     file, post the deep-lane comment and fall through to the merge below. On fail, hand the
     blockers and majors to `/ansh-resolve` and go back to step 5. A new head clears `deep_lane_sha`.
   - Otherwise merge, pinned to the verified head: `gh pr merge <n> --squash --match-head-commit
     <sha>`. If a base-branch rule blocks a direct merge (e.g. the deploy-line-stopped ruleset), arm
     `--squash --auto --match-head-commit <sha>` so a later head can't merge unverified.
     If branch protection needs a non-author approval, request CODEOWNERS, post the
     awaiting-approval comment, arm `--auto` and keep watching. Outcome `awaiting_approval`.
9. **Log and stop.** After a merge, approve the memory drafts for the PR's tasks
   (`ansh-memory approve-merged <task-ids>`), and save each agent default that merged uncorrected
   as a `convention` draft, per [memory](../_shared/memory.md). Set `merge_state: merged` in `plan.json` and log
   `ansh-log ansh-pr-loop merge merged --pr <n> --goal <g> --milestone <M-n> --surface <s>`. Write
   one outcome line ([outcomes](references/outcomes.md)). Unwatch the PR and stop the cadence.

## Cadence

- Use the host's PR watcher when there is one (T3 `watch_pull_request`; `unwatch_pull_request`
  at the end). Arm one watcher per PR and never a second scheduler on top.
- Else use session wakeups: `ScheduleWakeup` with exactly 300 seconds and the prompt
  `/ansh-pr-loop <n> reviewed via=<via>`. While a head build is running, arm a `Monitor` on it so
  its finish wakes the loop early. Check `TaskList` first so it isn't armed twice.
- Else poll in-session every 300 seconds, waiting in chunks of at most 60 seconds, checking for
  cancellation between them.
- Persist the reviewed head, lane, stuck-bot counters, retry record and iteration count in
  `.ansh/pr-loop-<n>.json` so a fresh fire picks them up.
- Not `CronCreate`: it can't carry state between fires. Never claim a wakeup was armed when the
  host has no tool for it. Tool names here are capabilities ([runtime](../_shared/runtime.md)).

## Edge cases

| Case | Do |
|---|---|
| Another loop already watches this PR | Don't start a second. Report and stop. |
| Several stacked PRs to drive | Work the lowest unmerged PR first. Read the ones above, but don't restart its checks for them. |
| A commit the loop didn't make lands on the branch | `/ansh-review pr <n>` runs the full gate for it before any merge. |
| Auto-merge armed and a new commit is about to be pushed | `gh pr merge <n> --disable-auto` first. Re-arm only after vitalize-agent passes the new head. |
| vitalize-agent hasn't reviewed the head | Don't merge, even with CI green. GitHub's `--auto` doesn't wait for it. |
| Converged except a human `CHANGES_REQUESTED` that `/ansh-resolve` re-requested | Keep watching. Outcome `awaiting_approval`. |
| Bot review stuck but a finding lacks a verified disposition | Don't dismiss. Let another iteration pass. |
| Failure outside the PR on a required check | Keep watching. Merge the base in once the base is green. |
| A dependency is parked or awaiting approval | This PR keeps its own lane. Drive it to green and hold with the `waiting-on` comment. |
| Same check or finding fails after 3 fix rounds | Stop with each attempt's evidence. Outcome `safety_cap`. |
| 12 iterations with work left and no progress | Stop and report what blocks. Outcome `safety_cap`. Waiting on a dependency or approval doesn't count. |
| Polling fallback and the PR is only waiting (dependency, approval) | Stop with the resume command. Outcome `waiting_on_parent` or `awaiting_approval`. |
| Ansh cancels | Stop. Outcome `stopped_by_user`. |
| Ansh says merge in his own message | Merge once converged and proved. Outcome `user_asked_merge`. |

## Output

Status line each iteration, then one final block:

```
PR_LOOP: DONE | PARKED | AWAITING_APPROVAL | WAITING | NOT_OWN | BLOCKED | STOPPED
PR: #<n> <url>   HEAD: <sha>   LANE: standard | deep
OUTCOME: <outcomes.jsonl value>   WAITING_ON: [#<n>]
GATE: <worst severity>, <n fixed>, agent defaults: <D-n ...>
EVIDENCE: <evidence comment or pack path>
NEXT: <exact command or click for Ansh, or none>
```

- **DONE**: merged. **PARKED**, **AWAITING_APPROVAL**, **WAITING**: verified and held, with why.
- **NOT_OWN**: someone else's PR, findings reported.
- **BLOCKED**: a missing tool or credential, or the safety cap. Name it.
- **STOPPED**: Ansh cancelled.
