#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re
from typing import List

# Preferred values for yes/no fields (i.e. all lowercase).
YES = "yes"
NO = "no"

# Pattern used to check if the entire string is "unknown", case-insensitive.
_PATTERN_UNKNOWN = re.compile(r"^unknown$", re.IGNORECASE)

# Pattern used to check if the entire string is functionally empty, i.e.
# empty string, or all characters are only whitespace.
_PATTERN_ONLY_WHITESPACE = re.compile(r"^\s*$")


def matches(pattern: re.Pattern, value: str) -> bool:
  """Returns whether the value matches the pattern."""
  return pattern.match(value) is not None


def is_empty(value: str) -> bool:
  """Returns whether the value is functionally empty."""
  return matches(_PATTERN_ONLY_WHITESPACE, value)


def is_unknown(value: str) -> bool:
  """Returns whether the value is 'unknown' (case insensitive)."""
  return matches(_PATTERN_UNKNOWN, value)


def quoted(values: List[str]) -> str:
  """Returns a string of the given values, each being individually quoted."""
  return ", ".join([f"'{entry}'" for entry in values])
