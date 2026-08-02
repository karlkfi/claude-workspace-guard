# Project Status

Single source of truth for progress and priorities in workspace-guard. Pick the next task from the top of the Queue.

**Status:** 🔲 ready · 🚫 blocked
**Size:** S = one session/PR · M = 2–3 sessions · L = needs a plan doc under `docs/plan/`
**Labels:** `security` `tests` `docs` `infra` `bug` `parsing`
**Next ID:** Q41

**Maintaining this file:** see [`docs/development/maintaining-backlog.md`](development/maintaining-backlog.md).

## Queue

Specific actionable items in priority order. Pick from the top; skip 🚫 items until their blocker clears.

| ID | Item | Labels | St | Sz | Notes |
|---|---|---|---|---|---|
| <a id="Q38"></a>Q38 | Stop `os.getuid()` crashing the hook on Windows | `bug` | 🔲 | S | `claude_tmp_root()` calls `os.getuid()`, absent on Windows, so the hook raises AttributeError once an interpreter starts. Pick the fallback after confirming where Claude Code puts that dir there. |
| <a id="Q39"></a>Q39 | Bind a `for` list glob built from an outer loop variable | `parsing` | 🔲 | S | `for d in docs/*; do for f in "$d"/*.md` — the inner item holds a `$` and poisons. Expand `loopmap` over the list before binding; the cross product is sound by issue 99's proxy argument. |

## Deferred

| ID | Item | Labels | Sz | Trigger to revive |
|---|---|---|---|---|
| <a id="Q23"></a>Q23 | Opt-in extra-roots for shared cross-worktree files | `security` | M | **Demand:** a session that legitimately needs cross-worktree shared files (mailbox files, the main checkout) and can't tolerate the prompts. Fix: an opt-in, empty-by-default extra-roots env var. |
| <a id="Q40"></a>Q40 | Catch a glob match that is itself a symlink out of the root | `security` | M | **Demand:** a glob-matched in-root name that points outside gets read silently. A glob resolves as the pattern, so `realpath` never sees the match. Closing it needs match enumeration. |
| <a id="Q35"></a>Q35 | Don't scan `$(…)` inside a quoted-delimiter heredoc body | `parsing` | S | **Demand:** spurious `ask` on a `cat <<'EOF'` body with a literal `$(…)`. `command_substitutions()` scans it though a quoted delimiter stops bash expanding it. Fix: skip quoted-delimiter bodies. |
