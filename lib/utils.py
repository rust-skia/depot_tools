# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

""" A collection of commonly used functions across depot_tools.
"""

import logging
import os
import re
import subprocess


def depot_tools_version():
  depot_tools_root = os.path.dirname(os.path.abspath(__file__))
  try:
    commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                          cwd=depot_tools_root).decode(
                                              'utf-8', 'ignore')
    return 'git-%s' % commit_hash
  except Exception:
    pass

  # git check failed, let's check last modification of frequently checked file
  try:
    mtime = os.path.getmtime(
        os.path.join(depot_tools_root, 'infra', 'config', 'recipes.cfg'))
    return 'recipes.cfg-%d' % (mtime)
  except Exception:
    return 'unknown'


def normpath(path):
  '''Version of os.path.normpath that also changes backward slashes to
  forward slashes when not running on Windows.
  '''
  # This is safe to always do because the Windows version of os.path.normpath
  # will replace forward slashes with backward slashes.
  path = path.replace(os.sep, '/')
  return os.path.normpath(path)


def ListRelevantFilesInSourceCheckout(files, root, match_re, exclude_re):
  """Finds all files that apply to a given set of source files, e.g. PRESUBMIT.

  If inherit-review-settings-ok is present right under root, looks for matches
  in directories enclosing root.

  Args:
    files: An iterable container containing file paths.
    root: Path where to stop searching.
    match_re: regex to match filename
    exclude_re: regex to exclude filename

  Return:
    List of absolute paths of the existing PRESUBMIT.py scripts.
  """
  files = [normpath(os.path.join(root, f)) for f in files]

  # List all the individual directories containing files.
  directories = {os.path.dirname(f) for f in files}

  # Ignore root if inherit-review-settings-ok is present.
  if os.path.isfile(os.path.join(root, 'inherit-review-settings-ok')):
    root = None

  # Collect all unique directories that may contain PRESUBMIT.py.
  candidates = set()
  for directory in directories:
    while True:
      if directory in candidates:
        break
      candidates.add(directory)
      if directory == root:
        break
      parent_dir = os.path.dirname(directory)
      if parent_dir == directory:
        # We hit the system root directory.
        break
      directory = parent_dir

  # Look for PRESUBMIT.py in all candidate directories.
  results = []
  for directory in sorted(list(candidates)):
    try:
      for f in os.listdir(directory):
        p = os.path.join(directory, f)
        if os.path.isfile(p) and re.match(match_re,
                                          f) and not re.match(exclude_re, f):
          results.append(p)
    except OSError:
      pass

  logging.debug('Presubmit files: %s', ','.join(results))
  return results
