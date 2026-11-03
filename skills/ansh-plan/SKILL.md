---
name: ansh-plan
description: "Turn a TDD, Linear ticket or prose goal into milestones and self-contained task packets, each with a red-first verification contract; harden a TDD first through two cross-model review loops. Use for /ansh-plan, /ansh-plan tdd <path>, or when a loop needs a plan, a backfill or a replan."
---

# /ansh-plan

**Goal:** a plan any agent can execute and verify without asking me anything.

**Uses:** [autonomy](../_shared/autonomy.md), [verification](../_shared/verification.md),
[milestones](../_shared/milestones.md), [principles](../_shared/principles.md),
[ledger](../_shared/ledger.md), [memory](../_shared/memory.md) (`../_shared/ansh-memory`), [runtime](../_shared/runtime.md),
[stacking](../_shared/stacking.md), [tickets](../_shared/tickets.md), [packet template](references/packet.md),
[plan.json](references/plan-json.md), [TDD review](references/tdd-review.md), `effort-dial`, `gold-star`, `lightweight-sql`,
`/ansh-small-loop`, `/ansh-loop`.

You write no code. Plan on Sonnet/Opus/Sol at high effort; a Deep goal uses `max` or the host's
highest supported equivalent. Use focused advisor help per runtime when needed; Fable/Astra never
own the plan or its child tasks. Take your time here: a sloppy plan makes every later round more
expensive.

## Modes

- **`/ansh-plan <goal>`**: the steps below.
- **`/ansh-plan tdd <path>`**: only [TDD review](references/tdd-review.md) on that TDD, then hand
  off. No packets. Use it when I hand you a TDD to review.

## Steps

1. **Gather context.**
   - Linear ticket (`REV-554`, a `linear.app` URL, or a `rev-554-*` branch): fetch it and its useful
     comments. Summarize in 2-3 sentences: the need, the constraints, the edge cases it names.
     Find the TDD from links on the ticket, its parents, or the project's documents.
   - Project or several tickets: fetch each. Keep IDs, titles and statuses.
   - Prose goal: use it as is. No Linear calls.
   - Move each in-scope ticket to In Progress per [tickets](../_shared/tickets.md).
   - Read the code deeply. Fan out `Explore` subagents over the subsystems, naming conventions and
     prior art. For each area the work touches, find the existing code to mirror: the gold-star.
     You can't write a packet for code you haven't read.
   - Read project memory per [memory](../_shared/memory.md) with the goal text, then each area
     it touches. Step 5 folds what applies into the packets. An area memory knew nothing about
     and you had to explore: save what you learned as a `workflow` draft with `--task` per memory.

2. **Phase 0: milestones and TDD checks.**
   - With a TDD that has no `.ansh/tdd-review.md` for its current version: run
     [TDD review](references/tdd-review.md) first, then plan from the reviewed local copy. Its
     changes go in the agent-drafted ticket comment below, never in the team's doc.
   - With a TDD: number AC, FM, D, Q and M IDs per [milestones](../_shared/milestones.md). Find the
     `Implementation milestones` section. Draft missing blocks from `PR order`, `File blast
     radius`, `Failure modes` and `Rollout`. Keep them in `plan.md` and post them as one comment on
     the goal's own ticket, marked agent-drafted. Never edit the team's TDD doc or `spec-doc.md`.
   - No TDD: write the same blocks in `plan.md` from the ticket. A small ticket is one milestone.
   - Run every check in the milestones Phase 0 table and apply its fix.
   - List each unknown that would change the decomposition: scope edges, data-model meaning,
     user-visible behavior, migration or deploy constraints. Settle each by running something.
     Otherwise take an agent default per [autonomy](../_shared/autonomy.md) and log it
     (`agent-default`).
   - Open `plan.md` with one paragraph: how you read the goal.

3. **Goal-level criteria.** Write three distinct, itemized lists, on every plan:
   - `guardrails`: lines the work never crosses, done or not. Out-of-scope areas, security and
     compliance lines, anything the ticket says not to touch. Always add the baseline: never push
     to `main`/`master`, never track `.ansh/`, and the never-do list in autonomy.
   - `acceptance_criteria`: the AC-n list, binary, inferred ones marked. Each answers "how would a
     person check this shipped right".
   - `exit_criteria`: autonomy's stop conditions, plus anything this goal's risk adds.

   The loops' scope gate, not this step, decides which loop runs.

4. **Decompose.**
   - Cut the smallest tasks that each end in a passing check. One milestone and one PR per task.
     Order by dependency.
   - Run `effort-dial` per task (5 axes, highest wins). Stamp model and effort from runtime's model
     table. Deep means not decomposed enough: split again.
   - Stamp `fresh_eyes`: `independent` by default; `review-fresh` for auth, payments, migrations,
     destructive or data-loss work; `swarm` for a new slice, a consolidation, or a refactor over
     ~10 files.
   - Stamp `autonomy: full` on every task. Add `parked_at_merge: true` where milestones or autonomy
     say the merge is irreversible.
   - Group tasks into `prs[]`: the smallest set of tight PRs, one layer each. If the goal collapses
     to one PR, write in `plan.md` why the layers can't be cut. Several PRs use the topology in
     [stacking](../_shared/stacking.md). Record each PR's `base` there too.
   - When the goal has tickets, every code task names one. Untracked work is pure scaffolding only;
     note it in `plan.md`.
   - Name every branch and write every `prs[].links` entry per [tickets](../_shared/tickets.md), so
     no later skill has to infer them.

5. **Make each packet ready.** A task leaves the planner only when all of these hold:
   - **Files named**, with what changes in each. Find them now.
   - **Gold-star found**: a `file:line` to mirror and why. Point at the slice of a `gold-star`
     reference when the goal has one.
   - **No open questions.** Each is answered, settled by a run, or an agent default.
   - **Memory folded in**: each project memory that applies is in Watch out for or Tests to
     write, citing its id.
   - **Edge cases written** into Watch out for and Tests to write: boundaries, empty, null and
     missing inputs, concurrency and ordering, timezone and DST, pagination, permissions, partial
     failure, idempotency and retries, large inputs.
   - **Naming and tracing** for a new repo, facade, service or business-logic fn: exact tag, class
     and `Effect.fn("<Tag>.<method>")` span per method, citing STYLE.md §13,
     `services-and-layers.md` and `repo-hygiene.md`. Match the package: flat tags in legacy
     `business-logic`, `"Feature/ServiceName"` in `packages/services`. Name the sibling to copy.
   - **Verification contract** per [verification](../_shared/verification.md): surface (derived
     from the files per its surface rule), covers,
     red-first checks with why each fails today, a real answer to "could this pass while broken",
     regression from blast radius and callers, perf, evidence path.
   - **Self-contained**: a fresh agent could run it from the packet alone.

   A box that won't close means split it, research it, or take a default.

6. **Persist to `.ansh/`.** Keep it, and any other agent scratch, out of git with the local
   exclude, never the tracked `.gitignore`:
   ```bash
   grep -qxF '.ansh/' "$(git rev-parse --git-path info/exclude)" || printf '\n.ansh/\n' >> "$(git rev-parse --git-path info/exclude)"
   ```
   - `plan.md`: your reading of the goal, the problem, architecture and data flow, constraints,
     a link to `decisions.md` (D-n live there), milestone blocks, the three lists, and
     the task index with deps. Add a feature-wide edge-case analysis. Push each edge case into the
     packet that owns it; leave cross-task ones flagged here for `/ansh-review goal`.
   - `plan.json` per [the schema](references/plan-json.md).
   - `tasks/<id>.md` per [the packet template](references/packet.md).
   - `discoveries.md` (specialists append) and `decisions.md` (the decision trail in autonomy).
   - Log `plan-written`.

7. **Challenge the plan.** Get an independent read-only reviewer per runtime, in challenge mode.
   Give it `plan.md`, `plan.json` and the packets, not your reasoning. Record its provider, model
   and independence in `plan.md`. It attacks the decomposition:
   - Missing tasks: migrations, backfills, flags, rollout and rollback, telemetry, tests, docs.
   - Wrong order or hidden dependencies.
   - Edge cases the feature-wide analysis missed. This is the highest-value attack.
   - Weak verification: could each verification pass while the feature is broken? A check that
     passes today, a wrong surface, a vibe instead of a command.
   - Deep work hiding as Standard, or a task too big to run from its packet.
   - Wrong layering: business logic in a repo, raw SQL outside a repo, an unblessed pattern.

   Fold real findings in, then re-run step 5 on what you touched. Note each rejected finding and
   why in `plan.md`. A product or scope question becomes an agent default. Log `challenge-done`.

## Re-entry

A specialist never changes direction. It appends to `discoveries.md` and returns `NEEDS_REPLAN`.
Loops also send you architectural REVISE findings and tasks that hit the iteration cap.

1. Read `discoveries.md`, the packet, and project memory for the area it hit.
2. Fold what was found into `plan.md` and the affected packets.
3. Mechanical gap (a path, a gold-star, a check you can settle from code): fix the packet and
   re-stamp. Change of direction: settle it by running something, else take an agent default.
   Record either in `decisions.md`.
4. Re-split if needed. Set `status` back to `todo`. Re-run step 5 and the challenge on what changed.

## Edge cases

| case | do |
|---|---|
| Linear call fails | Note it and go on. Ticket content the plan needs is missing: BLOCKED (runtime). |
| Needed work has no ticket (ticketed goal) | Create one under the parent so every task traces to a ticket. Prose goals skip this. |
| No ACs anywhere | Infer them, mark `inferred`, list them first in the report. |
| A Q-n or reviewer question is a product call | Agent default D-n with the alternative. Never ask. |
| Irreversible rollout or data-destroying merge | `parked_at_merge: true` on the milestone, PR and tasks. |
| Perf-sensitive milestone without a budget | Default budget from verification, noted. |
| A task won't split below Deep | Stamp Sonnet/Opus/Sol with high effort and the required verification; use advisor help per runtime if needed. Return DONE_WITH_CONCERNS naming it. |
| Diff will touch SQL or Drizzle | The packet tells the specialist to apply `lightweight-sql`. |
| Re-entry change of direction widens scope past the ticket | Do this ticket's share. Create a ticket for the rest. |
| Old plan lacks the three lists, milestones or Verification | Backfill them (steps 2, 3, 5), then challenge. |
| No delegation for the challenge | In-session adversarial pass, `independence: in-session`. Never call it independent. |
| TDD review: a model or `delegate_task` unavailable | BLOCKED for that loop. No silent model switch, no in-session substitute. |
| TDD review: 4 rounds without a clean round | Standalone: stop and check in. Inside a loop: plan from the latest version, DONE_WITH_CONCERNS. |
| TDD review: a finding is a product or scope call | Add it to the TDD's open questions; the plan takes an agent default for it. |
| Asked to run it now | Hand the plan to the loop the scope gate picks. Don't dispatch from here. |

## Output

`tdd` mode: the [TDD review](references/tdd-review.md#handoff) handoff, status **DONE** or
**BLOCKED**. Otherwise `.ansh/plan.md`, `plan.json`, `tasks/*.md`, `discoveries.md`, `decisions.md`. Then report:
the TDD review result if one ran, inferred ACs first, task count by tier (Deep should be zero), the challenge outcome and what it
changed, the three lists, agent defaults, parked-at-merge tasks, and the next command
(`/ansh-small-loop`, `/ansh-loop`, or `/ansh-task T1`).

Status: **DONE**, **DONE_WITH_CONCERNS** (name the task that stayed Deep), or **BLOCKED** (name what's
missing).
