# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

# The base names that are known to be Chromium metadata files.
_METADATA_FILES = {
    "README.chromium",
}


def is_metadata_file(path: str) -> bool:
  """Filter for metadata files."""
  return os.path.basename(path) in _METADATA_FILES
