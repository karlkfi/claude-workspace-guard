# Q39 — make the remaining Windows test failures pass

## Goal

Get `python -m unittest discover tests` to pass on Windows, and retire the
ratchet in `scripts/windows-ratchet.py` in favour of an ordinary gating job.

## Approach

There is no Windows box in this session, so the only ground truth is the
`unittest-windows` continuous integration (CI) job, which prints the full
`unittest` output. Work in rounds: read the failure list from CI, fix a
category, push, re-read. Every claim about Windows behaviour in this doc is
either quoted from a CI run or explicitly marked as an untested hypothesis.

Per case, decide whether the **fixture** or the **parser** is wrong. A fixture
that hard-codes a POSIX path is fixture noise; a parser that splits `C:\a` on
`:` is a real bug that would misfire on a real Windows install.

## Rounds

### Round 0 — collect the failure list

Baseline at branch point: `failures=56, errors=3` (see
`tests/windows-baseline.json`). The 3 errors are `KeyError: 'HOME'` and belong
to Q40, not here.

## Findings

_(filled in from CI output)_

## Scope guard

- Never raise `tests/windows-baseline.json`. Tighten it every round.
- No POSIX behaviour change: the Linux and macOS matrix must stay green.
- Secure-by-default holds — if a Windows fix would widen the allow set, it
  needs sign-off rather than a quiet default flip.
