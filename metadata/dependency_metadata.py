#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from typing import List, Tuple


class DependencyMetadata:
  """The metadata for a single dependency."""
  def __init__(self):
    self._entries = []

  def add_entry(self, field_name: str, field_value: str):
    self._entries.append((field_name, field_value.strip()))

  def has_entries(self) -> bool:
    return len(self._entries) > 0

  def get_entries(self) -> List[Tuple[str, str]]:
    return list(self._entries)
