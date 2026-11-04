#!/usr/bin/env bash
# collect.sh — deterministic facts for a sdlc-handoff handoff card.
# Portable: bash + git + POSIX utilities. No jq, no python.
# Usage: bash collect.sh [dir]
# Optional env:
#   HANDOFF_DIR            override the global handoff-card directory (default ~/.handoff)
#   HANDOFF_SESSION_DIRS   colon-separated directories to scan for *.jsonl session records
#   HANDOFF_SCRATCH_DIR    directory holding throwaway artifacts for this session
# Exit code is always 0: this script only reports, it never decides.

set -u

target_dir="${1:-$PWD}"
if [ -d "$target_dir" ]; then
	cd "$target_dir" 2>/dev/null || true
fi

handoff_dir="${HANDOFF_DIR:-$HOME/.handoff}"
session_dirs="${HANDOFF_SESSION_DIRS:-}"
scratch_dir="${HANDOFF_SCRATCH_DIR:-}"

max_status=40
max_diff=30
max_commits=8
max_sessions=3
max_handoffs=5
max_scratch=10

has_bsd_date=0
if date -r 0 '+%Y' >/dev/null 2>&1; then
	has_bsd_date=1
fi

fmt_date() {
	if [ "$has_bsd_date" = "1" ]; then
		date -r "$1" '+%Y-%m-%d %H:%M' 2>/dev/null
	else
		date -d "@$1" '+%Y-%m-%d %H:%M' 2>/dev/null
	fi
}

file_mtime() {
	if [ "$has_bsd_date" = "1" ]; then
		stat -f '%m' "$1" 2>/dev/null
	else
		stat -c '%Y' "$1" 2>/dev/null
	fi
}

section() {
	printf '== %s ==\n' "$1"
}

tmp="$(mktemp 2>/dev/null)" || tmp="/tmp/sdlc-handoff-collect.$$"
trap 'rm -f "$tmp"' EXIT

section "now"
date '+%Y-%m-%dT%H:%M:%S%z'

section "cwd/project"
printf 'cwd: %s\n' "$PWD"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -n "$repo_root" ]; then
	printf 'project_root: %s\n' "$repo_root"
	printf 'branch: %s\n' "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
	printf 'head: %s\n' "$(git rev-parse --short HEAD 2>/dev/null)"
	upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
	if [ -n "$upstream" ]; then
		counts="$(git rev-list --left-right --count "$upstream...HEAD" 2>/dev/null || true)"
		printf 'upstream: %s (behind/ahead: %s)\n' "$upstream" "${counts:-unknown}"
	else
		printf 'upstream: none\n'
	fi
else
	printf 'git: not a git repo\n'
fi

section "changes"
if [ -n "$repo_root" ]; then
	dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
	printf 'dirty_files: %s\n' "${dirty:-0}"
	printf -- '--- git status --porcelain (max %s) ---\n' "$max_status"
	git status --porcelain 2>/dev/null | head -n "$max_status"
	printf -- '--- git diff --stat (max %s) ---\n' "$max_diff"
	git diff --stat 2>/dev/null | head -n "$max_diff"
else
	printf 'no version control; recent files (mtime < 1 day, max 20):\n'
	find . -type f -not -path './.git/*' -not -path './node_modules/*' -mtime -1 2>/dev/null | head -n 20
fi

section "recent commits"
if [ -n "$repo_root" ]; then
	git log --oneline -n "$max_commits" 2>/dev/null
else
	printf 'not a git repo\n'
fi

section "sessions"
if [ -n "$session_dirs" ] && [ -n "$tmp" ]; then
	printf 'scanning: %s\n' "$session_dirs"
	: >"$tmp"
	old_ifs="$IFS"
	IFS=':'
	for d in $session_dirs; do
		[ -d "$d" ] || continue
		find "$d" -maxdepth 3 -type f -name '*.jsonl' ! -name '*.checkpoints.jsonl' -print0 >>"$tmp" 2>/dev/null
	done
	IFS="$old_ifs"
	if [ -s "$tmp" ]; then
		xargs -0 ls -1t <"$tmp" 2>/dev/null | head -n "$max_sessions" | while IFS= read -r f; do
			ts="$(file_mtime "$f")"
			printf '%s  %s\n' "$(fmt_date "${ts:-0}")" "$f"
		done
	else
		printf '(no session records found)\n'
	fi
else
	printf 'not configured (set HANDOFF_SESSION_DIRS to a colon-separated list)\n'
fi

section "handoffs"
: >"$tmp"
prev_dir=""
for d in "$PWD/.handoff" "$handoff_dir"; do
	[ -d "$d" ] || continue
	[ "$d" = "$prev_dir" ] && continue
	prev_dir="$d"
	find "$d" -maxdepth 1 -type f -name '*.md' -print0 >>"$tmp" 2>/dev/null
done
if [ -s "$tmp" ]; then
	xargs -0 ls -1t <"$tmp" 2>/dev/null | head -n "$max_handoffs" | while IFS= read -r f; do
		task_line="$(sed -n 's/^task:[[:space:]]*//p' "$f" 2>/dev/null | head -n 1)"
		status_line="$(sed -n 's/^status:[[:space:]]*//p' "$f" 2>/dev/null | head -n 1)"
		printf '%s  [%s]  %s\n' "$f" "${status_line:-unknown}" "${task_line:-no task field}"
	done
else
	printf '(no handoff cards yet)\n'
fi

section "temp artifacts"
if [ -n "$scratch_dir" ] && [ -d "$scratch_dir" ]; then
	printf 'dir: %s\n' "$scratch_dir"
	ls -A "$scratch_dir" 2>/dev/null | head -n "$max_scratch"
else
	printf 'not configured (set HANDOFF_SCRATCH_DIR; otherwise record it in section 8 of the card)\n'
fi

section "hints"
printf 'background tasks: check your tool set for running processes and record them in section 8\n'
printf 'never paste diffs into the card; point at file:line instead\n'

exit 0
