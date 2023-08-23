#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import textwrap
from typing import Dict, Union


_CHROMIUM_METADATA_PRESCRIPT = "Third party metadata issue:"
_CHROMIUM_METADATA_POSTSCRIPT = ("Check //third_party/README.chromium.template "
                                 "for details.")


class ValidationResult:
  """Base class for validation issues."""
  def __init__(self, message: str, fatal: bool):
    self._fatal = fatal
    self._message = message
    self._tags = {}

  def __str__(self) -> str:
    prefix = "ERROR" if self._fatal else "[non-fatal]"
    return f"{prefix} - {self._message}"

  def __repr__(self) -> str:
    return str(self)

  def is_fatal(self) -> bool:
    return self._fatal

  def set_tag(self, tag: str, value: str) -> bool:
    self._tags[tag] = value

  def get_tag(self, tag: str) -> Union[str, None]:
    return self._tags.get(tag)

  def get_all_tags(self) -> Dict[str, str]:
    return dict(self._tags)

  def get_message(self,
                  prescript: str = _CHROMIUM_METADATA_PRESCRIPT,
                  postscript: str = _CHROMIUM_METADATA_POSTSCRIPT,
                  width: int = 0) -> str:
    components = [prescript, self._message, postscript]
    message = " ".join(
        [component for component in components if len(component) > 0])

    if width > 0:
      return textwrap.fill(text=message, width=width)

    return message


class ValidationError(ValidationResult):
  """Fatal validation issue. Presubmit should fail."""
  def __init__(self, message: str):
    super().__init__(message=message, fatal=True)


class ValidationWarning(ValidationResult):
  """Non-fatal validation issue. Presubmit should pass."""
  def __init__(self, message: str):
    super().__init__(message=message, fatal=False)
