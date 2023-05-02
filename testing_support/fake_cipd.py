#!/usr/bin/env python3
# Copyright (c) 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import io
import os
import re
import shutil
import sys

ARCH_VAR = 'arch'
OS_VAR = 'os'
PLATFORM_VAR = 'platform'

CIPD_SUBDIR_RE = '@Subdir (.*)'
CIPD_ENSURE = 'ensure'
CIPD_EXPAND_PKG = 'expand-package-name'
CIPD_EXPORT = 'export'


def parse_cipd(root, contents):
  tree = {}
  current_subdir = None
  for line in contents:
    line = line.strip()
    match = re.match(CIPD_SUBDIR_RE, line)
    if match:
      print('match')
      current_subdir = os.path.join(root, *match.group(1).split('/'))
    elif line and current_subdir:
      print('no match')
      tree.setdefault(current_subdir, []).append(line)
  return tree


def expand_package_name_cmd(package_name):
  for v in [ARCH_VAR, OS_VAR, PLATFORM_VAR]:
    var = "${%s}" % v
    if package_name.endswith(var):
      package_name = package_name.replace(var, "%s-expanded-test-only" % v)
  return package_name


def main():
  cmd = sys.argv[1]
  assert cmd in [CIPD_ENSURE, CIPD_EXPAND_PKG, CIPD_EXPORT]
  # Handle cipd expand-package-name
  if cmd == CIPD_EXPAND_PKG:
    # Expecting argument after cmd
    assert len(sys.argv) == 3
    # Write result to stdout
    sys.stdout.write(expand_package_name_cmd(sys.argv[2]))
    return 0
  parser = argparse.ArgumentParser()
  parser.add_argument('-ensure-file')
  parser.add_argument('-root')
  args, _ = parser.parse_known_args()

  with io.open(args.ensure_file, 'r', encoding='utf-8') as f:
    new_content = parse_cipd(args.root, f.readlines())

  # Install new packages
  for path, packages in new_content.items():
    if not os.path.exists(path):
      os.makedirs(path)
    with io.open(os.path.join(path, '_cipd'), 'w', encoding='utf-8') as f:
      f.write('\n'.join(packages))

  # Save the ensure file that we got
  shutil.copy(args.ensure_file, os.path.join(args.root, '_cipd'))

  return 0


if __name__ == '__main__':
  sys.exit(main())
