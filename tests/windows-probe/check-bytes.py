"""Report the on-disk line endings of each variant, before anything is run.

Line endings are the variable under test, so a checkout that silently rewrote
them would invalidate every result below it.
"""
import pathlib
import sys

for path in sorted(pathlib.Path(__file__).parent.glob("*.cmd")):
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    lone_lf = raw.count(b"\n") - crlf
    print("%-28s CRLF=%-4d LF=%-4d %s" % (
        path.name, crlf, lone_lf,
        "mixed" if crlf and lone_lf else ("CRLF-only" if crlf else "LF-only")))

print("python %d.%d on %s" % (sys.version_info[0], sys.version_info[1],
                              sys.platform))
