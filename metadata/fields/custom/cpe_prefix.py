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

import metadata.fields.field_types as field_types
import metadata.fields.util as util
import metadata.validation_result as vr

_PATTERN_CPE_PREFIX = re.compile(r"^cpe:(2.3:|/).+:.+:.+(:.+)*$", re.IGNORECASE)


class CPEPrefixField(field_types.MetadataField):
  """Custom field for the package's CPE."""
  def __init__(self):
    super().__init__(name="CPEPrefix", one_liner=True)

  def validate(self, value: str) -> Union[vr.ValidationResult, None]:
    """Checks the given value is either 'unknown', or conforms to either the
    CPE 2.3 or 2.2 format.
    """
    if util.is_unknown(value) or util.matches(_PATTERN_CPE_PREFIX, value):
      return None

    return vr.ValidationError(
        reason=f"{self._name} is invalid.",
        additional=[
            "This field should be a CPE (version 2.3 or 2.2), or 'unknown'.",
            "Search for a CPE tag for the package at "
            "https://nvd.nist.gov/products/cpe/search.",
        ])
