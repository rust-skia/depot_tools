#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import re
import sys

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
# The repo's root directory.
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

# Add the repo's root directory for clearer imports.
sys.path.insert(0, _ROOT_DIR)

import metadata.fields.field_types as field_types
import metadata.fields.util as util
import metadata.validation_result as vr

_PATTERNS_NOT_MODIFIED = [
    # "None" and its variants, like "(none)", "none."
    re.compile(r"^\(?none\.?\)?\.?$", re.IGNORECASE),

    # "No modification" or "No modifications".
    re.compile(r"^no modifications?\.?$", re.IGNORECASE),

    # "N/A" and its variants, like "NA", "N/A", "N/A.".
    re.compile(r"^(N ?\/ ?A)\.?|na\.?$", re.IGNORECASE),

    # "Not applicable".
    re.compile(r"^not applicable\.?$", re.IGNORECASE),
]


class LocalModificationsField(field_types.FreeformTextField):
    """Custom field for local modification."""

    def __init__(self):
        super().__init__(name="Local Modifications", structured=False)

    def should_terminate_field(self, field_value) -> bool:
        field_value = field_value.strip()

        # If we can reasonably infer the field value means "No modification",
        # terminate this field to avoid over extraction.
        for pattern in _PATTERNS_NOT_MODIFIED:
            if pattern.match(field_value):
                return True

        return False
