#!/usr/bin/env vpython3
# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import sys
import unittest

if sys.version_info.major == 2:
  import mock
else:
  from unittest import mock

DEPOT_TOOLS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DEPOT_TOOLS_ROOT)

from testing_support import coverage_utils
from lib import utils


class GitCacheTest(unittest.TestCase):
  @mock.patch('subprocess.check_output', lambda x, **kwargs: b'foo')
  def testVersionWithGit(self):
    version = utils.depot_tools_version()
    self.assertEqual(version, 'git-foo')

  @mock.patch('subprocess.check_output')
  @mock.patch('os.path.getmtime', lambda x: 42)
  def testVersionWithNoGit(self, mock_subprocess):
    mock_subprocess.side_effect = Exception
    version = utils.depot_tools_version()
    self.assertEqual(version, 'recipes.cfg-42')

  @mock.patch('subprocess.check_output')
  @mock.patch('os.path.getmtime')
  def testVersionWithNoGit(self, mock_subprocess, mock_getmtime):
    mock_subprocess.side_effect = Exception
    mock_getmtime.side_effect = Exception
    version = utils.depot_tools_version()
    self.assertEqual(version, 'unknown')


class ListRelevantFilesInSourceCheckoutTest(unittest.TestCase):
  fake_root_dir = os.path.join(os.sep, 'foo', 'bar')
  _INHERIT_SETTINGS = 'inherit-review-settings-ok'

  def setUp(self):
    mock.patch('os.listdir').start()
    mock.patch('os.path.isfile').start()

  def testListRelevantPresubmitFiles(self):
    files = [
        'blat.cc',
        os.path.join('foo', 'haspresubmit', 'yodle', 'smart.h'),
        os.path.join('moo', 'mat', 'gat', 'yo.h'),
        os.path.join('foo', 'luck.h'),
    ]

    known_files = [
        os.path.join(self.fake_root_dir, 'PRESUBMIT.py'),
        os.path.join(self.fake_root_dir, 'foo', 'haspresubmit', 'PRESUBMIT.py'),
        os.path.join(self.fake_root_dir, 'foo', 'haspresubmit', 'yodle',
                     'PRESUBMIT.py'),
    ]
    os.path.isfile.side_effect = lambda f: f in known_files

    dirs_with_presubmit = [
        self.fake_root_dir,
        os.path.join(self.fake_root_dir, 'foo', 'haspresubmit'),
        os.path.join(self.fake_root_dir, 'foo', 'haspresubmit', 'yodle'),
    ]
    os.listdir.side_effect = (
        lambda d: ['PRESUBMIT.py'] if d in dirs_with_presubmit else [])

    presubmit_files = utils.ListRelevantFilesInSourceCheckout(
        files, self.fake_root_dir, r'PRESUBMIT.*', r'PRESUBMIT_test')
    self.assertEqual(presubmit_files, known_files)

  def testListUserPresubmitFiles(self):
    files = [
        'blat.cc',
    ]

    os.path.isfile.side_effect = lambda f: 'PRESUBMIT' in f
    os.listdir.return_value = [
        'PRESUBMIT.py', 'PRESUBMIT_test.py', 'PRESUBMIT-user.py'
    ]

    presubmit_files = utils.ListRelevantFilesInSourceCheckout(
        files, self.fake_root_dir, r'PRESUBMIT.*', r'PRESUBMIT_test')
    self.assertEqual(presubmit_files, [
        os.path.join(self.fake_root_dir, 'PRESUBMIT.py'),
        os.path.join(self.fake_root_dir, 'PRESUBMIT-user.py'),
    ])

  def testListRelevantPresubmitFilesInheritSettings(self):
    sys_root_dir = os.sep
    root_dir = os.path.join(sys_root_dir, 'foo', 'bar')
    inherit_path = os.path.join(root_dir, self._INHERIT_SETTINGS)
    files = [
        'test.cc',
        os.path.join('moo', 'test2.cc'),
        os.path.join('zoo', 'test3.cc')
    ]

    known_files = [
        inherit_path,
        os.path.join(sys_root_dir, 'foo', 'PRESUBMIT.py'),
        os.path.join(sys_root_dir, 'foo', 'bar', 'moo', 'PRESUBMIT.py'),
    ]
    os.path.isfile.side_effect = lambda f: f in known_files

    dirs_with_presubmit = [
        os.path.join(sys_root_dir, 'foo'),
        os.path.join(sys_root_dir, 'foo', 'bar', 'moo'),
    ]
    os.listdir.side_effect = (
        lambda d: ['PRESUBMIT.py'] if d in dirs_with_presubmit else [])

    presubmit_files = utils.ListRelevantFilesInSourceCheckout(
        files, root_dir, r'PRESUBMIT.*', r'PRESUBMIT_test')
    self.assertEqual(presubmit_files, [
        os.path.join(sys_root_dir, 'foo', 'PRESUBMIT.py'),
        os.path.join(sys_root_dir, 'foo', 'bar', 'moo', 'PRESUBMIT.py')
    ])


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.DEBUG if '-v' in sys.argv else logging.ERROR)
  sys.exit(
      coverage_utils.covered_main(
          (os.path.join(DEPOT_TOOLS_ROOT, 'git_cache.py')),
          required_percentage=0))
