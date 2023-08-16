#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import re
import sys
from typing import Union

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
# The repo's root directory.
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

# Add the repo's root directory for clearer imports.
sys.path.insert(0, _ROOT_DIR)

import metadata.fields.types as field_types
import metadata.fields.util as util
import metadata.validation_result as vr

_PATTERN_CPE_PREFIX = re.compile(r"^cpe:/.+:.+:.+(:.+)*$")


class CPEPrefixField(field_types.MetadataField):
  """Custom field for the package's CPE."""
  def __init__(self):
    super().__init__(name="CPEPrefix", one_liner=False)

  def validate(self, value: str) -> Union[vr.ValidationResult, None]:
    """Checks the given value is either 'unknown', or a valid
    CPE in the URI form `cpe:/<part>:<vendor>:<product>[:<optional fields>]`.
    """
    if util.is_unknown(value) or util.matches(_PATTERN_CPE_PREFIX, value):
      return None

    return vr.ValidationError(
        f"{self._name} is '{value}' - must be either 'unknown', or in the form "
        "'cpe:/<part>:<vendor>:<product>[:<optional fields>]'.")
