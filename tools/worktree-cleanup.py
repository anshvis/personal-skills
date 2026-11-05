#!/usr/bin/env python3
"""Find and remove git worktrees that nothing is using.

Dry run by default: prints what it would remove and why everything else is kept.
Pass --apply to remove. Branches are never deleted, and a worktree is kept if it:
  - has uncommitted or untracked changes (including inside submodules)
  - is the main checkout, is locked, or was modified within --min-age-hours
  - is the cwd of a running process or appears in a running command line
  - matches a --keep pattern (path or branch substring)
  - belongs to a T3 thread that is live, pending, scheduled, pinned, snoozed,
    or an open (unsettled, unarchived) top-level thread — when T3 is installed
If a worktree's HEAD commit is not on any branch or remote, a
cleanup-preserved/<sha> branch is created before removal so nothing is lost.

Usage:
  python3 worktree-cleanup.py                       # dry run, repos from T3
  python3 worktree-cleanup.py --repo ~/code/app     # dry run, explicit repos
  python3 worktree-cleanup.py --keep census --apply # remove, keep matches
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from pathlib import Path

T3_DB = Path.home() / ".t3/userdata/statev2.sqlite"
TERMINAL = {
    "runs": {"completed", "failed", "cancelled", "interrupted", "rolled_back"},
    "provider_sessions": {"stopped", "error", "failed"},
    "subagents": {"completed", "failed", "cancelled", "interrupted", "stopped"},
}
NOW = dt.datetime.now(dt.timezone.utc)


def run(args, timeout=60):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def parse_time(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def free_gib():
    st = os.statvfs(str(Path.home()))
    return round(st.f_bavail * st.f_frsize / 2**30, 2)


class T3State:
    """Read-only view of T3 thread state; empty when T3 isn't installed."""

    def __init__(self):
        self.threads, self.live, self.scheduled, self.projects = {}, set(), set(), []
        if not T3_DB.exists():
            return
        c = sqlite3.connect(T3_DB.as_uri() + "?mode=ro", uri=True, timeout=5)
        c.row_factory = sqlite3.Row

        def rows(sql):
            try:
                return list(c.execute(sql))
            except sqlite3.Error:
                return []

        self.projects = [r["workspace_root"] for r in rows(
            "select workspace_root from projection_projects where deleted_at is null")]
        for r in rows("select thread_id, archived_at, deleted_at, payload_json "
                      "from orchestration_v2_projection_threads"):
            self.threads[r["thread_id"]] = {**dict(r), "p": json.loads(r["payload_json"])}
        for table, terminal in TERMINAL.items():
            for r in rows(f"select thread_id, status from orchestration_v2_projection_{table}"):
                if r["status"] not in terminal:
                    self.live.add(r["thread_id"])
        for r in rows("select thread_id from orchestration_v2_projection_runtime_requests "
                      "where status = 'pending'"):
            self.live.add(r["thread_id"])
        self.scheduled = {r[0] for r in rows(
            "select thread_id from scheduled_tasks where enabled = 1")}

    def bindings(self, path):
        return [tid for tid, t in self.threads.items()
                if t["p"].get("worktreePath") == path and not t["deleted_at"]]

    def protection(self, tid, seen=None):
        """Reasons to keep a thread's worktree, inherited up the parent chain."""
        seen = seen if seen is not None else set()
        t = self.threads.get(tid)
        if tid in seen or not t:
            return set()
        seen.add(tid)
        p, open_ = t["p"], not t["archived_at"] and not t["deleted_at"]
        why = set()
        if tid in self.live:
            why.add("t3-live-agent-or-run")
        if tid in self.scheduled:
            why.add("t3-scheduled")
        if p.get("pinnedAt") and open_:
            why.add("t3-pinned")
        snooze = parse_time(p.get("snoozedUntil"))
        if snooze and snooze > NOW:
            why.add("t3-snoozed")
        parent = (p.get("lineage") or {}).get("parentThreadId")
        if parent:
            why |= self.protection(parent, seen)
        elif open_ and p.get("settledOverride") != "settled" and not p.get("settledAt"):
            why.add("t3-open-thread")
        return why


def list_worktrees(root):
    code, out, _ = run(["git", "-C", root, "worktree", "list", "--porcelain"])
    if code:
        return []
    items, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line:
            if cur.get("worktree"):
                items.append(cur)
            cur = {}
            continue
        key, _, value = line.partition(" ")
        cur[key] = value
    return items


def git_dirty(path):
    code, out, _ = run(["git", "-C", path, "status", "--porcelain=v1",
                        "--untracked-files=normal", "--ignore-submodules=none"], 120)
    return "unknown-status" if code else ("dirty" if out else None)


def inspect(roots, keep, min_age_hours, t3):
    _, lsof, _ = run(["/usr/sbin/lsof", "-nP", "-a", "-u", str(os.getuid()), "-d", "cwd", "-Fn"], 120)
    cwds = [x[1:] for x in lsof.splitlines() if x.startswith("n/")]
    _, ps, _ = run(["ps", "-axo", "command="])
    recent = NOW - dt.timedelta(hours=min_age_hours)
    results = []
    for root in roots:
        root = str(Path(root).expanduser().resolve())
        for wt in list_worktrees(root):
            path, branch = wt["worktree"], wt.get("branch")
            why = set()
            if path == root:
                why.add("main-checkout")
            if "locked" in wt:
                why.add("locked")
            if any(k in path or k in (branch or "") for k in keep):
                why.add("keep-pattern")
            if any(c == path or c.startswith(path + "/") for c in cwds):
                why.add("process-cwd")
            if path in ps:
                why.add("process-command")
            bound = t3.bindings(path)
            for tid in bound:
                why |= t3.protection(tid)
            p = Path(path)
            if not p.exists():
                why.add("missing-dir (run: git worktree prune)")
            elif dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc) > recent:
                why.add("recently-modified")
            if not why:
                state = git_dirty(path)
                if state:
                    why.add(state)
            results.append({"root": root, "path": path, "head": wt.get("HEAD"),
                            "branch": branch, "threads": bound, "keep": sorted(why)})
    return results


def remove(wt):
    root, path, head = wt["root"], wt["path"], wt["head"]
    # Re-check right before removal: work may have started since inspection.
    if git_dirty(path):
        return "kept-now-dirty", None
    t3 = T3State()
    if any(t3.protection(tid) for tid in t3.bindings(path)):
        return "kept-new-t3-work", None
    code, refs, _ = run(["git", "-C", root, "for-each-ref", "--contains", head,
                         "--format=%(refname)", "refs/heads", "refs/remotes"])
    if code:
        return "kept-ref-check-failed", None
    preserved = None
    if not refs.strip():
        preserved = f"cleanup-preserved/{head[:12]}"
        if run(["git", "-C", root, "branch", preserved, head])[0]:
            return "kept-preserve-failed", None
    code, _, err = run(["git", "-C", root, "worktree", "remove", path], 300)
    if code and "submodules" in err:
        # git refuses any worktree with submodules; force only when every
        # submodule is clean and its HEAD exists on a remote.
        check = ('test -z "$(git status --porcelain --untracked-files=normal)" && '
                 'test -n "$(git for-each-ref --contains HEAD --format=%\\(refname\\) refs/remotes)" '
                 '|| { echo "$displaypath"; exit 1; }')
        if run(["git", "-C", path, "submodule", "foreach", "--quiet", "--recursive", check], 300)[0]:
            return "kept-submodule-work", preserved
        code, _, err = run(["git", "-C", root, "worktree", "remove", "--force", "--force", path], 300)
    return ("removed" if code == 0 else f"blocked: {err.strip()[:200]}"), preserved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", default=[], help="repo root (repeatable); default: T3 projects")
    ap.add_argument("--keep", action="append", default=[], help="keep worktrees whose path/branch contains this")
    ap.add_argument("--min-age-hours", type=float, default=24)
    ap.add_argument("--apply", action="store_true", help="actually remove (default is dry run)")
    ap.add_argument("--report", default=str(Path.home() / "Library/Logs/worktree-cleanup-last-run.json"))
    args = ap.parse_args()

    t3 = T3State()
    roots = args.repo or t3.projects
    if not roots:
        ap.error("no T3 projects found; pass --repo PATH")
    before = free_gib()
    worktrees = inspect(roots, args.keep, args.min_age_hours, t3)
    candidates = [w for w in worktrees if not w["keep"]]

    print(f"Scanned {len(worktrees)} worktrees in {len(roots)} repos; {len(candidates)} removable.\n")
    print("KEEP:")
    for w in worktrees:
        if w["keep"]:
            print(f"  {w['path']}  [{', '.join(w['keep'])}]")
    print("\nREMOVE:" if args.apply else "\nWOULD REMOVE (dry run, pass --apply):")
    for w in candidates:
        if args.apply:
            w["outcome"], w["preserved_ref"] = remove(w)
            print(f"  {w['outcome']:<14} {w['path']}" + (f"  (saved {w['preserved_ref']})" if w["preserved_ref"] else ""))
        else:
            print(f"  {w['path']}  ({(w['branch'] or 'detached').removeprefix('refs/heads/')})")

    if args.apply:
        for root in {w["root"] for w in worktrees}:
            run(["git", "-C", root, "worktree", "prune"])
        removed = sum(w.get("outcome") == "removed" for w in candidates)
        after = free_gib()
        print(f"\nRemoved {removed}/{len(candidates)}. Free disk {before} -> {after} GiB.")
        report = Path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"checked_at": NOW.isoformat(), "free_gib_before": before,
                                      "free_gib_after": after, "worktrees": worktrees}, indent=2) + "\n")
        os.chmod(report, 0o600)
        print(f"Report: {report}")


if __name__ == "__main__":
    main()
