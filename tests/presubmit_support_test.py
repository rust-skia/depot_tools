#!/usr/bin/env python3
# Copyright 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os.path
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import gclient_utils
import presubmit_support


class PresubmitSupportTest(unittest.TestCase):
    def test_environ(self):
        self.assertIsNone(os.environ.get('PRESUBMIT_FOO_ENV', None))
        kv = {'PRESUBMIT_FOO_ENV': 'FOOBAR'}
        with presubmit_support.setup_environ(kv):
            self.assertEqual(os.environ.get('PRESUBMIT_FOO_ENV', None),
                             'FOOBAR')
        self.assertIsNone(os.environ.get('PRESUBMIT_FOO_ENV', None))


class TestParseDiff(unittest.TestCase):
    """A suite of tests related to diff parsing and processing."""

    def _test_diff_to_change_files(self, diff, expected):
        with gclient_utils.temporary_file() as tmp:
            gclient_utils.FileWrite(tmp, diff, mode='w+')
            content, change_files = presubmit_support._process_diff_file(tmp)
            self.assertCountEqual(content, diff)
            self.assertCountEqual(change_files, expected)

    def test_diff_to_change_files_raises_on_empty_file(self):
        with self.assertRaises(presubmit_support.PresubmitFailure):
            self._test_diff_to_change_files(diff='', expected=[])

    def test_diff_to_change_files_raises_on_empty_diff_header(self):
        diff = """
diff --git a/foo b/foo

"""
        with self.assertRaises(presubmit_support.PresubmitFailure):
            self._test_diff_to_change_files(diff=diff, expected=[])

    def test_diff_to_change_files_simple_add(self):
        diff = """
diff --git a/foo b/foo
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ b/foo
@@ -0,0 +1 @@
+add
"""
        self._test_diff_to_change_files(diff=diff, expected=[('A', 'foo')])

    def test_diff_to_change_files_simple_delete(self):
        diff = """
diff --git a/foo b/foo
deleted file mode 100644
index f675c2a..0000000
--- a/foo
+++ /dev/null
@@ -1,1 +0,0 @@
-delete
"""
        self._test_diff_to_change_files(diff=diff, expected=[('D', 'foo')])

    def test_diff_to_change_files_simple_modification(self):
        diff = """
diff --git a/foo b/foo
index d7ba659f..b7957f3 100644
--- a/foo
+++ b/foo
@@ -29,7 +29,7 @@
other
random
text
-  foo1
+  foo2
other
random
text
"""
        self._test_diff_to_change_files(diff=diff, expected=[('M', 'foo')])

    def test_diff_to_change_files_multiple_changes(self):
        diff = """
diff --git a/foo b/foo
index d7ba659f..b7957f3 100644
--- a/foo
+++ b/foo
@@ -29,7 +29,7 @@
other
random
text
-  foo1
+  foo2
other
random
text
diff --git a/bar b/bar
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ b/bar
@@ -0,0 +1 @@
+add
diff --git a/baz b/baz
deleted file mode 100644
index f675c2a..0000000
--- a/baz
+++ /dev/null
@@ -1,1 +0,0 @@
-delete
"""
        self._test_diff_to_change_files(diff=diff,
                                        expected=[('M', 'foo'), ('A', 'bar'),
                                                  ('D', 'baz')])

    def test_parse_unified_diff_with_valid_diff(self):
        diff = """
diff --git a/foo b/foo
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ b/foo
@@ -0,0 +1 @@
+add
"""
        res = presubmit_support._parse_unified_diff(diff)
        self.assertCountEqual(
            res, {
                'foo':
                """
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ b/foo
@@ -0,0 +1 @@
+add
"""
            })

    def test_parse_unified_diff_with_valid_diff_noprefix(self):
        diff = """
diff --git foo foo
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ foo
@@ -0,0 +1 @@
+add
"""
        res = presubmit_support._parse_unified_diff(diff)
        self.assertCountEqual(
            res, {
                'foo':
                """
new file mode 100644
index 0000000..9daeafb
--- /dev/null
+++ foo
@@ -0,0 +1 @@
+add
"""
            })

    def test_parse_unified_diff_with_invalid_diff(self):
        diff = """
diff --git a/ffoo b/foo
"""
        with self.assertRaises(presubmit_support.PresubmitFailure):
            presubmit_support._parse_unified_diff(diff)


if __name__ == "__main__":
    unittest.main()
