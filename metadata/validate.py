#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
from typing import List, Tuple

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
# The repo's root directory.
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, ".."))

# Add the repo's root directory for clearer imports.
sys.path.insert(0, _ROOT_DIR)

import metadata.parse
import metadata.validation_result as vr


def validate_file(filepath: str,
                  repo_root_dir: str) -> List[vr.ValidationResult]:
  """Validate the metadata file."""
  if not os.path.exists(filepath):
    result = vr.ValidationError(f"'{filepath}' not found.")
    result.set_tag(tag="reason", value="file not found")
    return [result]

  # Get the directory the metadata file is in.
  parent_dir = os.path.dirname(filepath)

  results = []
  dependencies = metadata.parse.parse_file(filepath)
  for dependency in dependencies:
    results.extend(
        dependency.validate(
            source_file_dir=parent_dir,
            repo_root_dir=repo_root_dir,
        ))

  return results


def check_file(filepath: str,
               repo_root_dir: str) -> Tuple[List[str], List[str]]:
  """Run metadata validation on the given file, and return all validation
  errors and validation warnings.

  Args:
    filepath: the path to a metadata file,
              e.g. "/chromium/src/third_party/libname/README.chromium"
    repo_root_dir: the repository's root directory; this is needed to construct
                   file paths to license files.

  Returns:
    error_messages: the fatal validation issues present in the file;
                    i.e. presubmit should fail.
    warning_messages: the non-fatal validation issues present in the file;
                      i.e. presubmit should still pass.
  """
  error_messages = []
  warning_messages = []
  for result in validate_file(filepath, repo_root_dir):
    # Construct the message.
    if result.get_tag("reason") == "file not found":
      message = result.get_message(postscript="", width=60)
    else:
      message = result.get_message(width=60)

    # TODO(aredulla): Actually distinguish between validation errors and
    # warnings. The quality of metadata is currently being uplifted, but is not
    # yet guaranteed to pass validation. So for now, all validation results will
    # be returned as warnings so CLs are not blocked by invalid metadata in
    # presubmits yet.
    # if result.is_fatal():
    #   error_messages.append(message)
    # else:
    warning_messages.append(message)

  return error_messages, warning_messages
