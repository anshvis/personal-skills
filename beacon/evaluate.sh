#!/usr/bin/env bash
# Turn recent agent sessions (every harness) into Beacon memory drafts with the Jev evaluator.
# Drafts wait in the queue for /ansh-retro; nothing is approved here. Never prints the key.
# Key: TYPESAFE_API_KEY or BEACON_JEV_API_KEY, else the macOS keychain item "ansh-jev-api-key".
# usage: beacon/evaluate.sh [--dry-run] [--since RFC3339] [--limit N]
set -uo pipefail

STATE="$HOME/.local/state/ansh-skills"
LAST="$STATE/beacon-eval-last"
mkdir -p "$STATE"
say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) beacon-evaluate: $*"; }

BEACON="$(command -v beacon 2>/dev/null || echo "$HOME/.local/bin/beacon")"
[ -x "$BEACON" ] || { say "beacon not installed, skipped"; exit 0; }

dry=(); since=""; limit="${BEACON_EVAL_LIMIT:-50}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) dry=(--dry-run); shift ;;
    --since) since="${2:-}"; shift 2 ;;
    --limit) limit="${2:-50}"; shift 2 ;;
    *) say "unknown flag $1"; exit 2 ;;
  esac
done

key="${TYPESAFE_API_KEY:-${BEACON_JEV_API_KEY:-}}"
if [ -z "$key" ] && command -v security > /dev/null 2>&1; then
  key="$(security find-generic-password -s ansh-jev-api-key -w 2>/dev/null || true)"
fi
[ -n "$key" ] || { say "no Jev key (keychain item ansh-jev-api-key), skipped"; exit 0; }

if [ -z "$since" ]; then
  since="$(cat "$LAST" 2>/dev/null || true)"
  [ -n "$since" ] || since="$(date -u -v-1d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)"
fi
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# No --project: each trace's memory is scoped to the repo it ran in.
# Beacon's 10s default times out on large traces, and the 03:00 run often fires as the laptop wakes
# before the network is up, so allow longer per call and retry once after a pause.
evaluate() {
  TYPESAFE_API_KEY="$key" "$BEACON" memory evaluations run --evaluator jev --since "$since" --limit "$limit" \
    --timeout "${BEACON_EVAL_TIMEOUT:-90s}" ${dry[@]+"${dry[@]}"}
}
if evaluate || { say "retrying in 60s"; sleep 60; evaluate; }; then
  [ "${#dry[@]}" -eq 0 ] && printf '%s\n' "$now" > "$LAST"
  say "done since $since"
else
  say "evaluation failed since $since (left the window open for the next run)"
  exit 1
fi
