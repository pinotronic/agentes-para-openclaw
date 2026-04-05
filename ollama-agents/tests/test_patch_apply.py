"""Tests for patch application safety fallbacks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.patch_apply import apply_diff_manually


def test_apply_diff_manually_new_file(tmp_path):
    diff = """--- /dev/null
+++ b/docs/hello.txt
@@ -0,0 +1,2 @@
+hello
+world
"""

    ok, message = apply_diff_manually(tmp_path, diff)

    assert ok is True, message
    assert (tmp_path / "docs" / "hello.txt").read_text(encoding="utf-8") == "hello\nworld"


def test_apply_diff_manually_rejects_path_traversal(tmp_path):
    diff = """--- /dev/null
+++ b/../../escape.txt
@@ -0,0 +1 @@
+nope
"""

    ok, message = apply_diff_manually(tmp_path, diff)

    assert ok is False
    assert "escapes project root" in message


def test_apply_diff_manually_rejects_existing_file_diff(tmp_path):
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-old
+new
"""

    ok, message = apply_diff_manually(tmp_path, diff)

    assert ok is False
    assert "only supports new-file diffs" in message