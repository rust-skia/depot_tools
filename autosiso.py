#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
Developers invoke this script via autosiso or autosiso.bat to simply run
Siso builds.
"""

import sys

import reclient_helper
import siso


def main(argv):
  with reclient_helper.build_context(argv) as ret_code:
    if ret_code:
      return ret_code
    argv = [
        argv[0],
        'ninja',
        # Do not authenticate when using Reproxy.
        '-project=',
        '-reapi_instance=',
    ] + argv[1:]
    return siso.main(argv)


if __name__ == '__main__':
  try:
    sys.exit(main(sys.argv))
  except KeyboardInterrupt:
    sys.exit(1)
