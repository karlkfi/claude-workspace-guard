"""Stub hook script: proves the shim launched a Python 3 and passed stdin through.

The real guard calls os.getuid() and dies on Windows before emitting anything
(Q38), so it can't tell a working shim from a broken one.
"""
import sys

sys.stdout.write("PROBE_OK python=%d.%d argv=%r stdin=%r\n" % (
    sys.version_info[0], sys.version_info[1], sys.argv[1:], sys.stdin.read()))
