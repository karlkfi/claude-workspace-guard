# Q51 — guard the PowerShell tool on Windows

**Status: not started.** Filed by Q44's validation pass; see
[`q44-windows-validation.md`](q44-windows-validation.md) finding 2.

## Goal

Stop native-Windows sessions from running shell commands this plugin never sees.

## The gap

Claude Code has two shell tools. Which one a Windows session gets is decided by
whether Git for Windows happens to be installed:

| configuration | shell tool | guarded today |
|---|---|---|
| Windows, no Git for Windows | `PowerShell` | **no** |
| Windows, Git for Windows | `Bash` (Git Bash) | yes |
| Windows, either, `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` | `PowerShell` | **no** |
| macOS / Linux / WSL | `Bash` | yes |

`hooks/hooks.json` matches `Bash`, the edit tools, and the read tools. `main()`
dispatches on `tool_name` and has no `PowerShell` branch. So in the first and
third rows the guard is installed, reports itself as active, and checks no shell
command at all. The native file tools stay guarded throughout, which is what
makes this easy to miss: `Read` and `Write` still prompt, so the plugin looks
like it is working.

Anthropic's documentation calls Git for Windows "optional" and says the
PowerShell tool is "rolling out progressively" where Git Bash *is* installed —
so this is not an exotic configuration, and a session can move into it without
the user changing anything.

## Why this isn't a one-line matcher addition

Adding `PowerShell` to the `hooks.json` matcher would route the command into
`handle_bash`, which tokenizes with `shlex` in POSIX mode. PowerShell is not a
POSIX shell, and the differences all fall in the unsafe direction:

- The escape character is a backtick, not a backslash; `shlex` reads
  `C:\Users\x` as escapes and yields `C:Usersx`, which resolves *inside* the
  workspace. That is a silent allow, and it is the common case, not an edge.
- Reads and writes are cmdlets (`Get-Content`, `Set-Content`, `Out-File`,
  `Add-Content`, `Copy-Item`, `Remove-Item`) with their own parameter grammar
  (`-Path`, `-LiteralPath`, `-Destination`), plus aliases that collide with the
  `SPEC` table's names (`cat`, `type`, `gc` for `Get-Content`; `sc` for
  `Set-Content`).
- Argument-mode vs expression-mode parsing, `@()`/`$()` subexpressions, and
  `&`/`.` invocation have no `SPEC` analogue.

So this needs its own `SPEC`-equivalent table, not a reuse of the Bash one — and
the repo's rule against aliasing a tool onto a row whose flag set diverges (see
Q3 on `rg`) applies with force here.

## The decision to make first

Secure-by-default says an unparseable command at the boundary should not be
silently allowed. But the guard's standing rule is the opposite — defer on
uncertainty, so normal permissions apply — and deferring on every PowerShell
command is exactly today's behaviour.

Three candidate shapes, to settle before writing code:

1. **Parse a subset, defer on the rest.** Matches the existing philosophy and
   ships incrementally. Leaves an unparsed tail permanently unguarded.
2. **Parse a subset, `ask` on the rest.** Secure by default, but prompts on
   every unrecognised command, which is most of them early on.
3. **Detect and warn.** Emit a one-time notice that shell commands are
   unguarded in this configuration and point at Git for Windows.

These are not exclusive: 3 is cheap and useful under either 1 or 2.

## Acceptance criteria

- A `PowerShell` matcher in `hooks/hooks.json` and a `PowerShell` branch in
  `main()` that never routes a PowerShell command through the POSIX tokenizer.
- `Get-Content`/`Set-Content`/`Out-File` and their aliases reach the same
  outside-workspace verdict as `cat`/`tee` do under Bash, with native paths
  (`C:\Users\…`) surviving tokenization intact.
- Fixtures for the backslash-escape case above, asserting no silent allow.
- README's Limitations entry on Windows shell coverage updated or removed.
