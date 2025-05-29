# Copyright 2025 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import subprocess
import sys

_NO_CAFFEINATE_FLAG = '--no-caffeinate'


def run(cmd, env=None):
    """Runs a command with `caffeinate` if it's on macOS."""
    if sys.platform == 'darwin':
        if _NO_CAFFEINATE_FLAG in cmd:
            cmd.remove(_NO_CAFFEINATE_FLAG)
        else:
            cmd = ['caffeinate'] + cmd
            print(
                f"\033[33mBuilding with `caffeinate`. Use {_NO_CAFFEINATE_FLAG} to disable it.\033[0m"
            )
    return subprocess.call(cmd, env=env)
