# Windows probe for the hook launcher

Throwaway diagnostic branch, not a pull request. It answers one question:

**Is the LF-only polyglot in [#94](https://github.com/karlkfi/claude-workspace-guard/pull/94) safe on cmd.exe, or safe by luck?**

cmd.exe resolves `goto :label` and `call :label` by seeking to a byte offset.
In an LF-only batch file that seek can land mid-line, so label lookup fails.
The launcher uses `call :try_interp` and `goto :found`, so it sits squarely in
that case. It has been observed working on one Windows 11 machine, but if the
failure is offset-dependent then it works by accident of line lengths and can
break when someone adds a line.

The variants here separate "works" from "works reliably", and check two
candidate fixes.

## Why a stub instead of the guard

`build_context()` calls `claude_tmp_root()`, which calls `os.getuid()`, which
does not exist on Windows. The real guard raises `AttributeError` before
emitting a decision, so it cannot distinguish a working launcher from a broken
one. `probe.py` stands in: it prints a marker and echoes stdin.

A success looks like:

```
PROBE_OK python=3.12 argv=[] stdin='{"ping":1}'
```

Anything else is a failure. Record the exact text and the exit code. The two
signatures worth naming are `The system cannot find the batch label specified`
(the seek hypothesis confirmed) and a silent exit with no output at all.

## The variants

| File | What it is |
|---|---|
| `variant-current.cmd` | The launcher exactly as it stands on the PR branch. LF-only, uses labels. |
| `variant-pad01.cmd`, `variant-pad07.cmd`, `variant-pad13.cmd` | Identical logic with 1, 7 and 13 filler lines inserted after `@echo off`, shifting every byte offset below them. |
| `variant-labelfree.cmd` | Candidate A. Same probe order, no `goto` and no `call :label`, so nothing seeks. LF-only. |
| `variant-mixed.cmd` | Candidate B. Byte-identical logic to `variant-current.cmd`, but the batch section and both heredoc delimiter lines use CRLF while the shell half stays LF. |

`variant-mixed.cmd` is pinned `-text` in `.gitattributes` so Git leaves its
bytes alone on checkout. Run `check-bytes.py` first and confirm that: if the
checkout normalized it, every result below is meaningless.

There is deliberately no `run-all.cmd`. A driver batch file would be subject to
the same line-ending hazard and would confound the results. Run each line by
hand.

## Procedure

Run from the repository root. Report the full output and exit code of every
command, including the ones that succeed.

### 0. Checkout state

```
git config core.autocrlf
git rev-parse --short HEAD
python tests\windows-probe\check-bytes.py
```

Expected: everything `LF-only` except `variant-mixed.cmd`, which must say
`mixed`. If `variant-current.cmd` reports CRLF, stop and say so — the
`.gitattributes` pin failed and that is itself the finding.

### 1. cmd.exe, one line per variant

Open a plain `cmd.exe` (not PowerShell, not Windows Terminal's PowerShell
profile) and run each of these separately, recording output and `%ERRORLEVEL%`:

```
echo {"ping":1} | tests\windows-probe\variant-current.cmd probe.py
echo %ERRORLEVEL%
```

```
echo {"ping":1} | tests\windows-probe\variant-pad01.cmd probe.py
echo %ERRORLEVEL%
```

```
echo {"ping":1} | tests\windows-probe\variant-pad07.cmd probe.py
echo %ERRORLEVEL%
```

```
echo {"ping":1} | tests\windows-probe\variant-pad13.cmd probe.py
echo %ERRORLEVEL%
```

```
echo {"ping":1} | tests\windows-probe\variant-labelfree.cmd probe.py
echo %ERRORLEVEL%
```

```
echo {"ping":1} | tests\windows-probe\variant-mixed.cmd probe.py
echo %ERRORLEVEL%
```

The perturbation set is the decisive one. If all four of current/pad01/pad07/
pad13 print `PROBE_OK`, LF-only survives byte-offset shifts and the hazard is
not reachable here. If any of them fails while the others pass, LF-only is
luck and has to go.

### 2. Git Bash

```
echo '{"ping":1}' | tests/windows-probe/variant-current.cmd probe.py; echo "exit=$?"
echo '{"ping":1}' | tests/windows-probe/variant-labelfree.cmd probe.py; echo "exit=$?"
echo '{"ping":1}' | tests/windows-probe/variant-mixed.cmd probe.py; echo "exit=$?"
```

`variant-mixed.cmd` is the one at risk here: its heredoc delimiter carries a
carriage return, and the shell has to match it. If it prints `PROBE_OK`, the
mixed layout is viable on both sides.

### 3. The no-interpreter path

In a cmd.exe with Python removed from PATH:

```
set "PATH=C:\Windows\system32;C:\Windows"
echo {"ping":1} | tests\windows-probe\variant-current.cmd probe.py
echo %ERRORLEVEL%
echo {"ping":1} | tests\windows-probe\variant-labelfree.cmd probe.py
echo %ERRORLEVEL%
```

Expected for both: exit 1, and both `NOT enforcing` lines on stderr. A silent
exit here is the failure the whole PR exists to prevent.

### 4. Data for Q38, while you are on the box

```
python -c "import os,tempfile;print(tempfile.gettempdir());print(os.environ.get('TEMP'));print(hasattr(os,'getuid'))"
dir "%TEMP%" | findstr /i claude
```

And the crash itself, for the record:

```
echo {"tool_name":"Bash","cwd":".","tool_input":{"command":"type ..\\q94-fake-target"}} | python scripts\bash-workspace-guard.py
```

Expected: `AttributeError: module 'os' has no attribute 'getuid'`. The target
is a synthetic name that does not exist; do not substitute a real path.

## What the answers decide

- All of current/pad01/pad07/pad13 pass: the hazard is not reachable on this
  build of cmd.exe. Keep the launcher as it stands, keep the LF pin.
- Any padded variant fails while `variant-labelfree.cmd` passes: take
  candidate A. One line-ending rule for the file, nothing seeks.
- Label-free fails but `variant-mixed.cmd` passes on both cmd.exe and Git
  Bash: take candidate B, and change `.gitattributes` from `text eol=lf` to
  `-text`.
