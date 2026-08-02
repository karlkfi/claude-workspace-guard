: << 'CMDBLOCK'
@echo off
REM Candidate A: the same probe order with no labels.
REM
REM cmd.exe resolves goto/call :label by seeking to a byte offset, which is the
REM construct that misbehaves in an LF-only batch file. Collecting the winner in
REM a variable instead means nothing seeks, so LF-only stops mattering and the
REM file keeps one line-ending rule for both halves.

setlocal
if "%~1"=="" (
    echo run-python-hook.cmd: missing script name >&2
    exit /b 1
)

set "HOOK_DIR=%~dp0"
set "HOOK_SCRIPT=%HOOK_DIR%%~1"

if not exist "%HOOK_SCRIPT%" (
    echo run-python-hook.cmd: script not found: %HOOK_SCRIPT% >&2
    exit /b 1
)

REM Probe interpreters by executing them, not by testing for their presence.
set "INTERP="
for %%I in ("py -3" "python" "python3") do (
    if not defined INTERP (
        %%~I -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >nul 2>nul && set "INTERP=%%~I"
    )
)

if not defined INTERP (
    echo run-python-hook.cmd: no working Python 3 interpreter found (tried py -3, python, python3). >&2
    echo run-python-hook.cmd: this guard is NOT enforcing. Install Python 3 and ensure it is on PATH. >&2
    exit /b 1
)

%INTERP% "%HOOK_SCRIPT%"
exit /b %ERRORLEVEL%
CMDBLOCK

# --- POSIX path -------------------------------------------------------------
# Unchanged from the shim on the PR branch.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"

if [ ! -f "${SCRIPT_DIR}/${SCRIPT_NAME}" ]; then
    echo "run-python-hook.cmd: script not found: ${SCRIPT_DIR}/${SCRIPT_NAME}" >&2
    exit 1
fi

for interp in python3 python; do
    command -v "$interp" >/dev/null 2>&1 || continue
    if "$interp" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' \
        >/dev/null 2>&1; then
        exec "$interp" "${SCRIPT_DIR}/${SCRIPT_NAME}"
    fi
done

echo "run-python-hook.cmd: no working Python 3 interpreter found (tried python3, python)." >&2
echo "run-python-hook.cmd: this guard is NOT enforcing. Install Python 3 and ensure it is on PATH." >&2
exit 1
