---
name: ansh-review
description: "Give an independent PASS, REVISE or DEBUG verdict on a task, a PR or a whole goal by rerunning its verification at the head SHA, checking it against the plan, rating blast radius and picking a merge lane. Use for /ansh-review task <id>, pr <n> or goal, from /ansh-cycle, /ansh-pr-loop or a loop."
---

# /ansh-review

**Goal:** an independent verdict with evidence. Never edit code.

**Uses:** [runtime](../_shared/runtime.md), [autonomy](../_shared/autonomy.md),
[verification](../_shared/verification.md), [principles](../_shared/principles.md),
[stacking](../_shared/stacking.md), [ledger](../_shared/ledger.md) (`../_shared/ansh-log`),
[/ansh-verify](../ansh-verify/SKILL.md), [/ansh-control](../ansh-control/SKILL.md),
[/codex](../codex/SKILL.md), [/review-fresh](../review-fresh/SKILL.md),
[/thermo-nuclear-code-quality-review](../thermo-nuclear-code-quality-review/SKILL.md),
[/ansh-debug](../ansh-debug/SKILL.md), [/ansh-plan](../ansh-plan/SKILL.md),
[/ansh-correct](../ansh-correct/SKILL.md), [memory](../_shared/memory.md), [PR gate](references/gate.md),
[blast radius](references/blast-radius.md), [output format](references/output.md).

Review on a fresh-context Sonnet/Opus/Sol per runtime at high effort. The deep lane uses `xhigh`
or the host's highest supported equivalent. Haiku/Luna are excluded from default routing;
explicit user model requests follow runtime. Fable/Astra may advise through the host advisor
mechanism only; they do not own a review lens. Preserve every required lens and verification check.

## Modes

- **`task <id>`**: one packet at its head SHA. Run the judgment steps below. `/ansh-cycle` calls it.
- **`pr <n>`**: the PR review gate in [gate](references/gate.md): reuse rules, four lenses in fresh
  subagents, one severity scale, the gate comment and head bookkeeping. The judgment steps run as
  one lens, `pr <n> gate`, at PR scope. `/ansh-pr-loop` calls it whenever the head moves.
- **`goal`**: the whole goal at the integration head (or the single PR's head). The loops call it
  once every task has passed. On top of the judgment steps:
  - Judge every `acceptance_criteria[]` item as written, not a paraphrase, plus
    `definition_of_done` and the cross-task edge cases `plan.md` flagged for this evaluation.
  - Rerun verification with `/ansh-verify run plan` at the head.
  - Step 8's independent pass is always cross-model when the host allows it.
  - Auth, payments, migrations, destructive work or a high blast radius take the deep lane.
  - At most two goal evaluations per goal ([autonomy](../_shared/autonomy.md#stop-conditions)).
    Count earlier ones from the ledger. A third call returns BLOCKED.
  - Every failure is an `ACT_ON` item routed to `ansh-plan` as new work.

## Steps

1. **Triage (cheap).** Read the diff, tickets and TDD, not the code in depth. Run plan gap (step 5)
   and blast radius (step 6) first. They pick the lane, and the lane picks how deep the rest goes.
2. **Ground in the repo.** Read the root `AGENTS.md`, the nearest nested one, and the sections of
   `.agents/skills/best-practices/references/` the diff touches. For Effect, use
   `bunx effect-solutions show <topic>` and `submodules/effect`. Before calling a pattern wrong,
   check the nearest good sibling slice. Matching a good neighbor isn't a finding. Matching a
   known-bad one still is: cite the reference doc. Read project memory per
   [memory](../_shared/memory.md) with the diff summary. A diff that repeats an approved
   `correction` or breaks a `convention` is Act on, citing the memory id.
3. **Rerun verification.** Don't trust the author's evidence. Run `/ansh-verify run` with the
   contract at the head SHA. Then judge it:
   - **Strength.** Could it pass while the feature is broken? If yes, Act on (`weak-verification`).
     Rerun a check on the base when red-first evidence is missing or doubtful. For a change with a
     `ui` half, drive the changed screen yourself with `/ansh-control` once.
   - **Surface.** Re-derive the surface from the diff per
     [verification](../_shared/verification.md#surface). A half the packet didn't declare is Act on
     (`wrong-surface`), and the check set is widened before any PASS.
   - **Loop closure.** Apply [closing the loop](../_shared/verification.md#closing-the-loop).
     Record `LOOP_CLOSURE: closed` only with criterion-to-evidence links and affected-caller
     coverage. Missing proof is Act on (`weak-verification`); strengthen it before PASS.
   - **Not a pass** per [verification](../_shared/verification.md#not-a-pass).
4. **Does it work?** Read done-criteria from the packet (or what you were handed). Each gets a
   verdict with evidence. No evidence is a fail. Every "Watch out for" item must be handled and
   every "Tests to write" test must exist and pass: a miss is Act on. Then look for edge cases the
   planner missed. These layering problems are Act on (`services-and-layers.md`, STYLE.md §13):
   - A repo doing more than data access: auth checks, business decisions, tagging rows with domain
     meaning, merging across tables, opening orchestration transactions, calling another repo or a
     facade, publishing events, or returning transport errors.
   - Database access outside a repo. A facade calling another slice's repo instead of its facade.
   - An effectful repo or facade method that isn't `Effect.fn("<Tag>.<method>")`, or a service tag
     that doesn't match its class name.

   A brand-new slice in `packages/database` instead of `packages/services` is Consider.
5. **Is it what we planned?** Find the plan, closest source first: the packet and `plan.json`
   (including the `prs[]` entry); the Linear tickets the PR links (keys `[A-Z]{2,5}-\d+` from the
   title, body, branch and commits; note closes vs part of); each ticket's parents and their other
   children; the TDD (a design-doc link, else the Linear project's documents).

   For a closed ticket, each AC is met (cite line or test), partial or missing. For a "part of"
   ticket, check only this share. The change stays inside the parent's scope, takes no sibling or
   later-phase work, matches the TDD's names, data model, interfaces, code location and phase, and
   holds nothing the TDD lists as out of scope. Rate the gap: **none**; **small** (a naming
   difference, a missing test or small case, with an obvious fix); **large** (a missing core
   criterion, a contradiction of the TDD, extra scope, or a decision the plan never made).
6. **What breaks if it's wrong?** Rate kind and blast radius per [blast radius](references/blast-radius.md).
7. **Merge lane and park.**
   - `merge_lane: deep` when blast radius is high. The deep lane is defined in autonomy's merge
     rule; run it here with a fresh-context review and an independent re-verification at the head.
     No fresh context available: BLOCKED.
   - `merge_lane: standard` otherwise.
   - `parked: yes` when the task, milestone or PR has `parked_at_merge: true`, or merging would do
     something on autonomy's never-do list.
   - List each `Depends on #<n>` with its state. Open or parked ones go in `WAITING_ON`. They change
     when it merges, not the verdict.
8. **Independent review.** Skip the outside reviewer on `gate`. Otherwise send intent, criteria,
   watch-outs, plan sources and the diff (not the author's reasoning) to an independent reviewer
   per runtime. Record provider, model and independence. Do your own adversarial pass too: races,
   missing error paths, leaks, security boundaries. Add a fresh-context review on the deep lane or
   when the packet says `fresh_eyes: review-fresh`; on a stacked or shared branch give it
   `git diff origin/<base>...HEAD` instead of running `/review-fresh` (stacking). Large structural
   diffs or `fresh_eyes: swarm` add the `pr-review-*` lenses. Verify each finding against the code.
9. **Synthesize.** Merge findings on the same issue and note who raised each. Ones raised
   independently by two reviewers weigh most. Bucket each: **Act on** (a failing criterion or
   check, a real bug or security issue, a layering violation, a missed watch-out; blocks),
   **Consider** (legitimate, unsure it's worth it now; gold-star divergence goes here or Noted),
   **Noted**, **Dismissed** (with a one-line reason). Settle a disagreement by running something.
   Never drop an independent finding silently.
10. **Verdict and log.** Emit the block in [output](references/output.md) with its `MODE`. Post or
    edit the merge-call comment when a PR exists and it's ours. Log
    `ansh-log ansh-review verdict <PASS|REVISE|DEBUG> --task <id> --pr <n> --reason <r> --surface <s>`
    (phase `goal-verdict` in goal mode).
11. **Repeat mistakes.** Log each Act on item with a `reason` and a `--class`, reusing an existing
    class when it's the same mistake (ledger). A class seen twice goes in `REPEAT_CLASSES`.

## Edge cases

| case | do |
|---|---|
| A plan source is missing, or no ticket or TDD | Review against what exists. Name what's missing in `PLAN_SOURCES`. |
| Large plan gap | REVISE routed to `/ansh-plan`. Not Act on by itself: the plan may be wrong. A missing core criterion still fails step 4. |
| Code deliberately differs and beats a stale plan | Still a large gap. Route to `/ansh-plan` to update the plan. Don't touch code. |
| Packet has no `## Verification` | Rerun the done-criteria. Flag `weak-verification` as Act on. |
| Author's evidence at a different SHA | Ignore it. Your rerun at the head SHA is the evidence. |
| Behavior wrong, cause not obvious | DEBUG. List it in `BUGS`. No blind patch. |
| Reviewers still disagree after running something | Keep both sides in Consider. Set the lane to deep. |
| No delegation available | In-session pass, `independence: in-session`, noted in `CONCERNS`. |
| Deep lane or `review-fresh` needed, no fresh context | BLOCKED. |
| Dependency PR open or parked | `WAITING_ON`. Review anyway. |
| Verification needs prod writes or a deploy | Don't. Mark the check skipped with the reason and set `parked: yes`. |
| Someone else's PR | Read-only: no comments, no bookkeeping ([gate](references/gate.md)). |

## Output

The block in [output](references/output.md), plus the principles that changed a call. End with
**DONE** (verdict emitted) or **BLOCKED** (couldn't evaluate; say what's needed).
