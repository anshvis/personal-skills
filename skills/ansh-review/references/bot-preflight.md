# Bot pre-flight

Predicts what the repo's review bot will mark blocking or refuse to approve, so the loop fixes it
before the bot sees the head. In `vitalizecare/web-app` the bot is `vitalize-agent[bot]`. It
requests changes on any `**issue (blocking):**` finding, approves only when there is none, and
never approves a diff that touches a gated path. Every push it reviews costs a round-trip of about
30 minutes, and it can raise new findings on unchanged code. So the cheapest fix is the one made
before the push.

It runs as the `bot-preflight` lens of the [gate](gate.md), and on its own as
`/ansh-review pr <n> preflight` on a local head before a push. It reads the code and never edits it.

## Inputs

Read each from the **base branch**, because the bot runs from the base branch's copy, so a PR
can't change its own reviewer.

1. **The bot's rules.**
   - `.agents/skills/best-practices/SKILL.md`, the Non-Negotiables above all, and every reference
     under `references/` that covers a file the diff touches.
   - In `.buildkite/pipelines-ci-cd/pr-checks/pr-review/context/`, the extra context files
     `context-map.ts` routes the changed paths to. For example `grafana.md`, `infra.md`,
     `migrations.md` or `cluster-projections.md`.
   - The nearest `AGENTS.md` of every touched folder.
   - In another repo, find the bot's prompt and context files first. If there are none, say so in
     `CONCERNS` and use the repo's best-practices docs.
2. **The approval gate.** `context/NO_AUTO_APPROVE_PATHS.ts`. A diff that touches a matching path
   never gets the bot's approval, whatever it finds.
3. **Calibration.** The bot's recent blocking findings on this repo. Never pass `--paginate`, which
   walks the repo's whole comment history.
   ```bash
   for p in 1 2 3; do  # the newest 300 review comments: about 20 to 30 blocking findings
     gh api "repos/<owner>/<repo>/pulls/comments?sort=created&direction=desc&per_page=100&page=$p" \
       -q '.[] | select(.user.login=="vitalize-agent[bot]" and (.body|test("issue \\(blocking\\)")))
           | "\(.pull_request_url|split("/")|last) \(.path) :: \(.body|split("\n")|map(select(test("blocking")))|first)"'
   done
   ```
   Group them by the rule they cite. They show what the bot actually blocks on, which can be more
   or less than the rules say. Also list the ledger's `bot-preflight-miss` classes
   (`ansh-log` events, phase `bot-preflight-miss`). They are the misses this lens made before. Check
   each one against this diff by name.
4. **This PR's history.** Every earlier bot finding on this PR, and our reply to it. A finding
   already answered with a verified disposition is likely to come back on the next head (the bot
   doesn't read replies), so plan the pre-emptive answer now.

## What to check

Run these checks on `git diff origin/<base>...<sha>`, which is the PR's own share of a stacked branch:

| Check | A predicted blocker when |
|---|---|
| Gated paths | A changed file matches the approval gate. Was it meant? A hand-edited generated file (for example a `*durations.json` shard table that only a cron may write), a stray CI or `infra/` edit, or a file that belongs in another PR: fix it by dropping the change. A real infra or CI change: no fix, but report `human-approval-required` so the loop requests a human reviewer at once instead of waiting for an approval that won't come. |
| Spec in `apps/docs` | Behavior, a contract, a flag mode, an operator script or a rollout step changed, and no `apps/docs` page covers it. The rule is "No behavior, contract, or domain change without updating the relevant spec in `apps/docs`." Also check that no existing page now says something false, such as "remains future work" or an old flow. |
| Non-Negotiables | Every one, against the added lines: N+1 (a per-item repo, service or DB call in a loop over a hospital-scale collection), raw `Date` or `new Date()` outside a boundary, `pg.Client` or SQL outside a repo, a `.Test` or mock layer in shipped code, an explicit `any` or `unknown` cast, swallowed errors (`catchAll` or `catchAllCause` that hides what failed), a repo doing more than data access, a missing `Effect.fn` name. |
| Tests | New behavior with no test, a test named for a ticket instead of the behavior, a fixture that can't fail. |
| Calibration classes | Each class from the calibration corpus and from `bot-preflight-miss`, checked against the diff by name. |

Verify each candidate in the code before you report it, and rate its likelihood: `likely` (it
breaks a rule as written, so fix it), `possible` (a reviewer that matches on patterns would flag
it, but it holds up on a careful read), or `unlikely` (leave it out).

## Output

Rows for the gate, in its severity scale:

| Row | Severity | Route |
|---|---|---|
| `likely` predicted blocker | blocker, source `bot-preflight` | `/ansh-resolve` fixes it before the next push |
| A gated path changed by accident | blocker | drop the change |
| A real gated path | minor, `human-approval-required` | the loop requests a human reviewer now |
| `possible` predicted blocker with a cheap fix inside a changed file, such as a comment explaining why the loop is per person, or a boundary helper instead of `new Date` | major | fix it |
| `possible` with no cheap fix | minor | keep the pre-emptive reply text in the row, so `/ansh-resolve` can post it the moment the bot raises it |

Also return `PREFLIGHT: clean | <n> predicted blockers | human-approval-required: <paths>` for the
verdict block.

## Learning from misses

When the bot blocks on something this lens didn't predict for that head, `/ansh-pr-loop` logs it:

```bash
ansh-log ansh-review bot-preflight-miss REVISE --pr <n> --class <kebab-case rule> --reason review-comment --note "<path>: <one line>"
```

The next run reads those classes as calibration (input 3). A class missed twice goes to
`/ansh-correct` as a candidate lint or check, so the repo enforces the rule instead of the bot.
