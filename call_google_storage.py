#!/usr/bin/env python3
# Copyright (c) 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Download files from Google Storage, given the bucket and file."""

import optparse
import os
import re
import sys

import subprocess2

# Env vars that tempdir can be gotten from; minimally, this
# needs to match python's tempfile module and match normal
# unix standards.
_TEMPDIR_ENV_VARS = ('TMPDIR', 'TEMP', 'TMP')

GSUTIL_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'gsutil.py')

# Maps sys.platform to what we actually want to call them.
PLATFORM_MAPPING = {
    'cygwin': 'win',
    'darwin': 'mac',
    'linux': 'linux',  # Python 3.3+.
    'win32': 'win',
    'aix6': 'aix',
    'aix7': 'aix',
    'zos': 'zos',
}


def GetNormalizedPlatform():
    """Returns the result of sys.platform accounting for cygwin.
    Under cygwin, this will always return "win32" like the native Python."""
    if sys.platform == 'cygwin':
        return 'win32'
    return sys.platform


# Common utilities
class Gsutil(object):
    """Call gsutil with some predefined settings.  This is a convenience object,
    and is also immutable.

    HACK: This object is used directly by the external script
        `<depot_tools>/win_toolchain/get_toolchain_if_necessary.py`
    """

    MAX_TRIES = 5
    RETRY_BASE_DELAY = 5.0
    RETRY_DELAY_MULTIPLE = 1.3
    VPYTHON3 = ('vpython3.bat'
                if GetNormalizedPlatform() == 'win32' else 'vpython3')

    def __init__(self, path, boto_path=None):
        if not os.path.exists(path):
            raise FileNotFoundError('GSUtil not found in %s' % path)
        self.path = path
        self.boto_path = boto_path

    def get_sub_env(self):
        env = os.environ.copy()
        if self.boto_path == os.devnull:
            env['AWS_CREDENTIAL_FILE'] = ''
            env['BOTO_CONFIG'] = ''
        elif self.boto_path:
            env['AWS_CREDENTIAL_FILE'] = self.boto_path
            env['BOTO_CONFIG'] = self.boto_path

        if PLATFORM_MAPPING[sys.platform] != 'win':
            env.update((x, "/tmp") for x in _TEMPDIR_ENV_VARS)

        return env

    def call(self, *args):
        cmd = [self.VPYTHON3, self.path]
        cmd.extend(args)
        return subprocess2.call(cmd, env=self.get_sub_env())

    def check_call(self, *args):
        cmd = [self.VPYTHON3, self.path]
        cmd.extend(args)
        ((out, err), code) = subprocess2.communicate(cmd,
                                                     stdout=subprocess2.PIPE,
                                                     stderr=subprocess2.PIPE,
                                                     env=self.get_sub_env())

        out = out.decode('utf-8', 'replace')
        err = err.decode('utf-8', 'replace')

        # Parse output.
        status_code_match = re.search('status=([0-9]+)', err)
        if status_code_match:
            return (int(status_code_match.group(1)), out, err)
        if ('ServiceException: 401 Anonymous' in err):
            return (401, out, err)
        if ('You are attempting to access protected data with '
                'no configured credentials.' in err):
            return (403, out, err)
        if 'matched no objects' in err or 'No URLs matched' in err:
            return (404, out, err)
        return (code, out, err)

    def check_call_with_retries(self, *args):
        delay = self.RETRY_BASE_DELAY
        for i in range(self.MAX_TRIES):
            code, out, err = self.check_call(*args)
            if not code or i == self.MAX_TRIES - 1:
                break

            time.sleep(delay)
            delay *= self.RETRY_DELAY_MULTIPLE

        return code, out, err


def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-b',
                      '--bucket',
                      help='Google Storage bucket to fetch from.')
    parser.add_option('-p', '--file', help='Path of file to fetch.')
    parser.add_option('-o',
                      '--output',
                      help='Path where GCS contents should be downloaded.')
    parser.add_option('-e', '--boto', help='Specify a custom boto file.')
    (options, args) = parser.parse_args()

    file_url = 'gs://%s/%s' % (options.bucket, options.file)

    # Make sure gsutil exists where we expect it to.
    if os.path.exists(GSUTIL_DEFAULT_PATH):
        gsutil = Gsutil(GSUTIL_DEFAULT_PATH, boto_path=options.boto)
    else:
        parser.error('gsutil not found in %s, bad depot_tools checkout?' %
                     GSUTIL_DEFAULT_PATH)

    gsutil.check_call('cp', file_url, options.output)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
