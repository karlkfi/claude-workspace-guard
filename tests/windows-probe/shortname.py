"""Does the 8.3 short name from gettempdir() break the Q38 session-tmp allow?

smoochy measured `tempfile.gettempdir()` returning `C:\\Users\\ADMINI~1\\...` on
Windows 11 and flagged that comparing that prefix against a realpath-resolved
path would miss. PR #103 wraps the root in os.path.realpath, which on Windows
resolves short names via _getfinalpathname -- but only for paths that exist.

So the question is whether both sides land in the same form once a real
directory is there. Build the layout the guard actually matches and check.
"""
import os
import tempfile

tmp = tempfile.gettempdir()
print("gettempdir()            = %s" % tmp)
print("realpath(gettempdir())  = %s" % os.path.realpath(tmp))
print("short name in raw       = %s" % ("~" in tmp))

# claude_tmp_root() as PR #103 computes it.
root = os.path.realpath(os.path.join(tmp, "claude"))
print("claude_tmp_root()       = %s" % root)

# The path a background task would actually be read back from.
sess = "11111111-2222-3333-4444-555555555555"
leaf = os.path.join(tmp, "claude", "-c-proj", sess, "tasks")
os.makedirs(leaf, exist_ok=True)
target = os.path.join(leaf, "abc.output")
open(target, "w").close()

rp = os.path.realpath(target)
print("realpath(task output)   = %s" % rp)

# is_session_tmp_path(): inside the root AND carrying the session id.
inside = rp == root or rp.startswith(root + os.sep)
has_sess = sess in rp.split(os.sep)
print("startswith(root)        = %s" % inside)
print("session id is a segment = %s" % has_sess)
print("VERDICT                 = %s" % ("MATCH" if inside and has_sess else "MISS"))
