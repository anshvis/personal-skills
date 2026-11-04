# PR review gate

What `/ansh-review pr <n>` runs. The gate runs once per state of the PR's own code, and a comment
on the PR records it so later calls can reuse it.

## Ownership

Check the PR author against `gh api user -q .login`. Someone else's PR: run the gate read-only and
return the findings. No comment, no bookkeeping.

## Reuse a recorded gate (own PRs only)

Find the newest top-level comment whose body starts with
`<!-- ansh-pr-loop:review-gate head=<sha> -->`. List the PR's own commits since then:

```bash
git log --no-merges --format=%H <sha>..origin/<head-branch> --not origin/<base-branch> origin/main
```

The `--not` part drops commits that came in by merging `main` or the base.

| Finding | Do |
|---|---|
| Empty list | The PR's code is unchanged. Reuse the gate's rows. Say "reusing review gate from `<sha>`". |
| Header lacks a lens (`ansh-review`, `review-fresh`, `independent`, `thermo-nuclear`, `bot-preflight`) | Run only that lens, merge its rows in, and edit the comment. |
| Header says `ansh-review (triage)` only | Run the full gate and replace the comment. |
| Ticket, a parent ticket or the TDD has `updatedAt` after the gate's date | Re-run only the `/ansh-review` lens. The target moved even if the code didn't. |
| Any commit listed | Run the full gate again and edit the comment. |
| `<sha>` isn't in the branch history | Treat as changed. Run the full gate. |
| A commit the loop didn't make | Counts as a listed commit: full gate. |

Reuse across heads covers the `review-fresh` and Independent lenses only. Whenever the head
moves, rerun the `/ansh-review`, thermo-nuclear and `bot-preflight` lenses at the new head, including after
fix commits or base merges. `VERDICT`, `LOOP_CLOSURE`, `QUALITY`, `MERGE_LANE` and `PARKED` must
describe the current head. At an unchanged head, reuse a recorded thermo-nuclear result only
when its report identifies that SHA and meets the approval bar.

## Running the lenses

Pin one head SHA and give it to every lens. Each lens runs in its own fresh subagent
([runtime](../../_shared/runtime.md)). Brief each with: the pinned SHA, a read-only checkout or
`git diff origin/<base>...<sha>`, which skill file to read and apply, the output format below, and
that it must not edit, commit, push, post or delegate further (except `/review-fresh`'s own lens
subagents). The gate's own agent never reviews the code itself. It briefs, reads reports, merges
them, and posts.

| Lens | How |
|---|---|
| `/ansh-review` | `/ansh-review pr <n> gate` at the SHA: the judgment steps at PR scope. The `gate` flag skips step 8's outside reviewer, because the Independent lens below is that pass; it still does its own adversarial pass. Returns its verdict block ([output](output.md)). |
| `/review-fresh` | Its capture rebases, so run it in a detached temporary worktree at the SHA, diffing against `origin/<base>`. Argument: the PR title as intent. |
| Independent | Per runtime's independent review, with the PR intent and riskiest areas as watch-outs. Record provider, model and independence. Label findings `independent`. |
| `bot-preflight` | Brief a subagent to read [bot pre-flight](bot-preflight.md) and apply it at the SHA: the repo bot's rules from the base branch, its approval-gate paths, and its recent blocking findings as calibration. It returns predicted-blocker rows and the `PREFLIGHT` line. |
| `/thermo-nuclear-code-quality-review` | It sets `disable-model-invocation`, so the Skill tool can't load it. Brief a background subagent to read `../thermo-nuclear-code-quality-review/SKILL.md` and apply it to the diff. Return findings as presumptive-blocker, major or minor with `path:line`. |

A lens the host can't run is marked `unavailable` in the header, never run by the gate's own agent.
A missing fresh-context lens when the lane is deep is BLOCKED. An unavailable thermo-nuclear
lens blocks auto-merge in every lane. Populate `QUALITY` from its report; resolve or justify its
findings with evidence under that skill's approval bar. An agent default alone is insufficient.

## One severity scale

Collapse duplicates. Keep the strictest severity and both sources.

| Severity | From |
|---|---|
| blocker | `/ansh-review` `ACT_ON` items and `BUGS` (route `/ansh-debug`); review-fresh `blocker`; an independent critical finding; a `bot-preflight` `likely` predicted blocker or an accidental gated-path change; a thermo-nuclear presumptive blocker (a visible code-judo move left on the table, a file pushed past 1k lines, ad-hoc branching tangling a shared flow, scattered feature checks, an unneeded wrapper or cast contract, a duplicated helper or wrong layer) |
| major | review-fresh `major`; a `bot-preflight` `possible` finding with a cheap fix; another structural thermo-nuclear finding; an `/ansh-review` `PLAN_GAP: large` |
| minor | review-fresh `minor`; an independent advisory finding; a `bot-preflight` `possible` finding with no cheap fix (its pre-emptive reply attached) or `human-approval-required`; a thermo-nuclear legibility note; an `/ansh-review` `CONSIDER` item, `PLAN_GAP: small` or mixed kind |

`/ansh-review` `NOTED` and `DISMISSED` items don't become rows. Blockers and majors are the items
the caller hands to `/ansh-resolve`; a minor goes too only when it's cheap and inside files the PR
already changed.

## The gate comment

One top-level comment per PR. Edit the existing one instead of adding another. PR's own voice: no
AI attribution, no emoji, one plain line per finding, no raw reviewer output. Post the `/ansh-review`
lens's `<!-- ansh-review:merge-call -->` comment beside it ([output](output.md)).

```markdown
<!-- ansh-pr-loop:review-gate head=<full head sha> -->
**Review gate** for `<short sha>` (ansh-review + review-fresh + independent + thermo-nuclear + bot-preflight, <YYYY-MM-DD>)

Checked against: <FND-1234 (closes), parent FND-1200, TDD: <title + link> | no linked ticket>
Verdict: <PASS | REVISE | DEBUG>. Kind: <setup | logic | wiring>. Blast radius: <low | medium | high>. Lane: <MERGE_LANE>. Parked: <no | yes>

Loop closure: <closed, criteria and affected callers proved | open, missing proof and next checks>
Code quality: thermo-nuclear <pass | revise | unavailable> (<report and SHA>)
Bot pre-flight: <clean | n predicted blockers | human approval required: paths>
Worst severity: <blocker | major | minor | none>

| Severity | Source | Finding | Where |
|---|---|---|---|
| major | review-fresh | <what is wrong and the failure it causes> | `path:line` |
| major | ansh-review | <criterion or TDD section, and how the diff misses it> | `path:line` or ticket key |
| minor | independent | ... | ... |

<"Clean: no findings." when the list is empty>
```

## Head bookkeeping after fixes

When the caller passes `/ansh-resolve`'s report for gate items: mark each fixed row
`fixed in <sha>`, mark each agent default `agent default: <choice>`, and move `head=` to the pushed
fix commit. Those fixes do not trigger a full four-lens re-review, but rerun the `/ansh-review`,
thermo-nuclear and `bot-preflight` lenses at the pushed head before publishing a passing gate. They must confirm
the fixes and check for new behavioral or structural regressions. Any later non-merge commit
triggers the full gate.
