# TDD review

What `/ansh-plan tdd <path>` runs, and what step 2 runs before planning from a TDD: two independent
review loops on the TDD, one per model family, then a legibility pass. You edit the TDD here, and
only a local copy of it. Never edit code, tickets or the team's copy of the doc.

## Before round 1

- **Local file only.** If the TDD lives in Linear or Google Docs, export it to a local markdown file
  and review that. Never save back to the team's doc without my yes. Hand back the diff instead.
  Planning (step 2 onward) reads the reviewed copy.
- **Write the task from the problem, not the design.** One or two lines: who has what problem, and
  what we want to be true after. Source it from the ticket, its parent and the Linear project, not
  from the TDD. If the only source is the TDD itself, say so in the handoff.
- **Snapshots.** Save the TDD as it stands to `/tmp/<name>-original.md`. Before each round, save the
  current version to `/tmp/<name>-<loop>-r<N>.md`.
- **Findings log.** Keep `/tmp/<name>-findings.md`: one row per finding with loop, round, pass,
  model, the finding, evidence, and what was done with it. "What happened before:" sections, the
  round table and the handoff are all built from this file, never from memory.
- **Models.** Call `orchestrator_capabilities` once and take the provider and model IDs from it.
  Loop A: Codex `gpt-6-astra`, high reasoning (xhigh when the TDD touches auth, payments,
  payroll/pay rules, migrations, prod data or patient data). Loop B: Claude Opus 5.5
  (`claude-opus-5-5`). If either model isn't available, stop and say so. Don't switch models or
  fall back to an in-session pass: the point of this mode is independence.

## How each loop runs

- Start each reviewer with T3 `delegate_task` in this checkout. Use a new task and a distinct
  `clientRequestId` for every pass (`a-r1-simplify`, `b-r2-review`, ...). Follow the delegate's
  `next`; don't poll it.
- Reviewers only report. They don't edit files, commit, push, post anything, run migrations or DB
  resets, or start their own subagents.
- Each round has two passes, run one after the other: simplify, then review. The review pass reads
  the TDD after your simplify edits.
- Between passes, you edit the TDD. First check every claim a reviewer makes about the code against
  the code itself (read the file, grep, run the query or test). Settle a disagreement by running
  something, not by arguing. Also check findings against the root and nearest `AGENTS.md`, the
  best-practices references, and project memory ([memory](../../_shared/memory.md)). An approved
  `correction` or `convention` beats a reviewer's preference.
- Every finding gets one disposition in the findings log. Never drop one silently:
  - **applied**: what changed in the TDD.
  - **accepted as a risk**: why, and what would make it worth revisiting.
  - **rejected**: the reason, with evidence (`path:line`, command output). Push back on any finding
    that's wrong, and don't apply it.
  - **open**: a product or scope call the code can't settle. It goes into the TDD's open questions,
    not a guess.
- Fix what's real and keep looping. Don't stop after one round to ask me which findings to fix.
- A loop ends when both passes come back clean in the same round. A pass that led to any TDD edit
  isn't clean. If that hasn't happened after 4 rounds, stop and check in with me: show the trend per
  round and what's still coming up. Inside a loop run (`/ansh-small-loop`, `/ansh-loop`) don't stop
  the run: plan from the latest version, put the unresolved findings in `plan.md` as agent
  defaults, and finish DONE_WITH_CONCERNS.

## Loop B

- Start Loop B only after Loop A converges.
- Its round history lists every Loop A finding and what was done with each, as plain fact:
  "Loop A (Codex), round N: ..."
- Loop B can reopen anything Loop A settled, including accepted risks and rejected findings. Don't
  call Loop A's results reviewed or agreed. Don't tell Loop B it's a confirmation pass.
- If Loop B reverses a Loop A decision, apply it and flag it in the handoff. Don't re-run Loop A
  afterwards.

## Reviewer brief rules

Each brief is the task plus generic criteria and nothing else. Never include:

- a summary of the TDD or how the design works
- a checklist or a "look here" list built from its contents
- a custom definition of severity or of what counts as a blocker
- anything that protects the author's decisions, goals or accepted risks (no "these are
  deliberate", no "only report if it's worse than X")
- your own reasoning about a finding, or which findings you think are right

The TDD's goals and scope are open to review like everything else.

From round 2 on, and in every Loop B round, add "What happened before:" with every earlier finding
and what was done with it (applied / accepted as a risk, and why / rejected, and why / open). State
it as fact, with no argument for it.

### Simplify brief

```
Act as the review sub-agent for this task. You're a maintainer of this repository, checked out at
<path>. Don't edit any files, post anything anywhere, or start subagents. <Read-only tool access,
e.g. the linear CLI, gh, rg.>
Task: <task>
Simplify: find a simpler version of the design in <tdd path> that still covers the task. Reuse what
the codebase already has; cut anything the task doesn't need, goals included. Done when every part
is required by the task.
Report each cut or merge you'd make: what goes, why the task doesn't need it, and what replaces it,
if anything. If every part is already required by the task, say so.
<What happened before: ...>
```

### Review brief

```
Act as the review sub-agent for this task. You're a maintainer of this repository, checked out at
<path>. Don't edit any files, post anything anywhere, or start subagents. <Read-only tool access.>
Task: <task>
Review: review the design in <tdd path> as a maintainer of this repo would: correctness, failure
and recovery paths, consistency with neighboring code and conventions, and whether its claims about
the code are true. Questions the TDD already lists as open aren't findings. Report findings, most
severe first, with evidence. Done when a pass finds nothing.
<What happened before: ...>
```

## After both loops converge

1. **Coverage check (yours).** Read the source tickets once more. Every acceptance criterion maps to
   a TDD section, and the TDD holds nothing the tickets put out of scope. A gap is a finding: apply
   it and log it as `coverage`. Also rate the blast radius of what the TDD would ship
   ([blast radius](../../ansh-review/references/blast-radius.md)), so the handoff says which lane its PRs will need.
2. **Legibility pass.** Two Codex readers in parallel, same brief:
   "Read <tdd path> as an engineer on this team who is new to this project. Judge it as writing, not
   as a design: don't review the design itself, and don't edit any files. List every term used
   without being defined, used before it's defined, or used for two different things; every
   sentence too compressed to follow on first read; and every reference to a ticket, step, rule or
   question label the TDD doesn't explain. Standard engineering terms and Vitalize product names
   don't need definitions; healthcare and project terms do. For each item, quote the passage, say
   what's unclear, and suggest plainer wording. Most important first."
   Merge the two lists and apply the fixes. Wording only: if a fix would change what the design
   says, don't apply it. Log it as open. Then diff against the last loop snapshot to confirm only
   wording moved.
3. **Log.** `ansh-log ansh-plan tdd-review <CONVERGED|CHECK_IN|BLOCKED> --reason <r> --note
   "<loop A rounds>/<loop B rounds>"`, plus one `tdd-finding` event per applied finding with a
   `--class` (reuse an existing class for the same mistake) and `--model`. A class seen twice goes in
   the handoff's repeat classes.
4. **Hand off** with the block below. Copy it to `.ansh/tdd-review.md` so step 2 can tell the TDD
   was already reviewed.

## Handoff

```
MODE: tdd <path>
RESULT: CONVERGED | CHECK_IN (round 4, not converged) | BLOCKED - <why>
TASK: <the task line> | source: <tickets | TDD only>
MODELS: loop A <provider/model/effort> | loop B <provider/model/effort>
SNAPSHOTS: /tmp/<name>-original.md ... | findings log: /tmp/<name>-findings.md
BLAST_RADIUS: low | medium | high - <why, and the lane its PRs will need>
```

Then, in plain language:

1. **Results per round**, one table per loop: round, pass, findings, applied / accepted / rejected /
   open.
2. **What changed from the original and why**, grouped by section, not by round.
3. **What Loop B caught that Loop A missed**, and every place Loop B reversed Loop A.
4. **Accepted risks and judgment calls to check**: each with the reason and what would reopen it.
5. **Still open**: open questions added to the TDD, legibility fixes that would change the design,
   coverage gaps against the tickets.
6. **Repeat classes**, if any.

On CHECK_IN, lead with the trend per round and what's still coming up instead.
