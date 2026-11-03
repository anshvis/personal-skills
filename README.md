# personal-skills

Personal, provider-neutral skill sources: my `/ansh-*` skills, which take a ticket or TDD to a merged, verified PR without a human in the loop, the glue skills they call, and a few standalone helpers. `ANSH.md` is the index.

Public. Built for my own setup at work, so some skills assume that stack (web-app, Linear, Buildkite). Fork and adapt.

## Install for Claude Code, Cursor and Codex

```bash
git clone https://github.com/anshvis/personal-skills.git ~/personal-skills
~/personal-skills/setup.sh
```

Defaults to Claude, Cursor and Codex. Cursor gets the same complete catalog and shared
references under `~/.cursor/skills/`. Claude keeps the complete existing skill catalog under
`~/.claude/skills/` and its agent definitions under `~/.claude/agents/`. Codex and local ChatGPT coding sessions get the complete skill catalog, including every
`ansh-*` skill and every helper/nested workflow, under `~/.agents/skills/`. Claude links directly to the sources. Codex links to a complete local mirror outside the
Claude plugin directory so names stay plain, such as `$ansh-plan`. The mirror includes
the full runtime guide, CLI references and reviewer prompts. Re-run setup after source
updates to refresh it.
Existing conflicting entries are backed up outside skill discovery under
`~/.local/state/ansh-skills/backups/`. Re-running setup keeps matching links unchanged.

```bash
./setup.sh --dry-run
./setup.sh --providers claude,cursor        # Claude and Cursor only
./setup.sh --providers codex              # only Codex
```

Claude and Cursor: `/ansh-plan <goal>`, `/ansh-task T1`, `/ansh-review`, `/ansh-save`.
Codex: `$ansh-plan <goal>`, `$ansh-task T1`,
`$ansh-review`, `$ansh-save`, or select the
skill in the picker. Newly installed skills appear on the next turn; start a new session
if the picker has cached an older catalog. The local ChatGPT desktop coding runtime uses
these filesystem skills too. ChatGPT web workspace Skills have a separate installation
lifecycle; this local setup does not upload or publish the private repository.

[Runtime compatibility](skills/_shared/runtime.md) defines capability-based tool/model routing,
independent review and execution when Workflow is absent. Model profiles are recommendations;
a skill never changes the current model by declaring a tier. Missing services or a required
fresh-review capability are reported explicitly. No tmux, `/meta` or provider defaults are
installed by this setup.

## Tools

`tools/worktree-cleanup.py` removes git worktrees nothing is using, to reclaim disk on
machines where agents leave many behind. Dry run by default; pass `--apply` to remove.
It keeps dirty worktrees, the main checkout, locked or recently modified ones, anything a
running process uses, and anything tied to a live, pinned, snoozed or open T3 thread.
Branches are never deleted, and an unreferenced HEAD is saved as `cleanup-preserved/<sha>`
first.

```bash
python3 tools/worktree-cleanup.py                        # dry run over T3 projects
python3 tools/worktree-cleanup.py --repo ~/web-app       # or name repos explicitly
python3 tools/worktree-cleanup.py --keep census --apply  # remove, keeping matches
```

## Beacon (project memory)

`setup.sh` also runs `beacon/setup.sh` (skip it with `--no-beacon`). It installs
[Beacon](https://github.com/asymptote-labs/agent-beacon) from the release tarball (checksum
verified) into `~/.local/bin`, configures its local collector hooks for the selected hosts, and
registers its MCP server as `aw-beacon` in each selected host. Existing Cursor MCP servers
are preserved, and the config is backed up before adding Beacon. The collector and memory store stay on the machine; setup never signs
in or connects to Beacon Cloud. The optional nightly evaluator sends traces to Jev, as described below.

The `/ansh` skills use it as project memory through `skills/_shared/ansh-memory`: planning,
debugging and review read lessons from earlier runs, and verified root causes and reviewer
corrections are saved back. Rules in [memory](skills/_shared/memory.md). Memory lives in
`~/.beacon/`, per machine, and is never committed here.

Nightly drafts from every session: store a Jev key in the keychain, then re-run setup. It
schedules `beacon/evaluate.sh` daily at 03:00 (log in `~/.local/state/ansh-skills/beacon-eval.log`).
This sends session traces to Jev.

```bash
security add-generic-password -U -a "$USER" -s ansh-jev-api-key -w   # prompts for the key
./setup.sh
```

Cursor's [skill directories](https://cursor.com/docs/skills) and
[MCP configuration](https://cursor.com/docs/mcp) use the standard skill folders and `mcpServers`
JSON format. Restart Cursor after setup if its catalog has not refreshed. This installs local
skills; remote and Cloud agents need their own installation or repository-provided skills.

## Install as a plugin (Claude Code Web)

```
/plugin marketplace add anshvis/personal-skills
/plugin install ansh-personal@ansh-personal-skills
```

Skills are namespaced under the plugin, e.g. `/ansh-personal:ansh-loop`.

## Caveats
- The iteration ledger (`skills/_shared/ansh-log`) and memory helper (`skills/_shared/ansh-memory`) need `jq`. Without it, or without Beacon, they skip with a warning and nothing else breaks.
- Namespacing: skills that call each other by bare name (e.g. `/ansh-plan`) may need the `ansh-personal:` prefix.
- On Claude Code Web, plugin sub-agents and hooks are limited (fully supported in Desktop/Cowork), so the loop is degraded there.
- The loop's `.ansh/` scratch state is per-machine/sandbox and does not sync.
