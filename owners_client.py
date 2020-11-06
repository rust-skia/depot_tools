# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class OwnersClient(object):
  """Interact with OWNERS files in a repository.

  This class allows you to interact with OWNERS files in a repository both the
  Gerrit Code-Owners plugin REST API, and the owners database implemented by
  Depot Tools in owners.py:

   - List all the owners for a change.
   - Check if a change has been approved.
   - Check if the OWNERS configuration in a change is valid.

  All code should use this class to interact with OWNERS files instead of the
  owners database in owners.py
  """
  def __init__(self, host):
    self._host = host

  def ListOwnersForFile(self, project, branch, path):
    """List all owners for a file."""
    raise Exception('Not implemented')

  def IsChangeApproved(self, change_number):
    """Check if the latest patch set for a change has been approved."""
    raise Exception('Not implemented')

  def IsOwnerConfigurationValid(self, change_number, patch):
    """Check if the owners configuration in a change is valid."""
    raise Exception('Not implemented')
