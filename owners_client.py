# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

import owners
import scm


APPROVED = 'APPROVED'
PENDING = 'PENDING'
INSUFFICIENT_REVIEWERS = 'INSUFFICIENT_REVIEWERS'


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

  def GetChangeApprovalStatus(self, change_id):
    """Check the approval status for the latest patch in a change.

    Returns a map of path to approval status, where the status can be one of:
    - APPROVED: An owner of the file has reviewed the change.
    - PENDING:  An owner of the file has been added as a reviewer, but no owner
      has approved.
    - INSUFFICIENT_REVIEWERS: No owner of the file has been added as a reviewer.
    """
    raise Exception('Not implemented')

  def IsOwnerConfigurationValid(self, change_id, patch):
    """Check if the owners configuration in a change is valid."""
    raise Exception('Not implemented')


class DepotToolsClient(OwnersClient):
  """Implement OwnersClient using owners.py Database."""
  def __init__(self, host, root, branch):
    super(DepotToolsClient, self).__init__(host)
    self._root = root
    self._branch = branch
    self._db = owners.Database(root, open, os.path)
    self._db.override_files({
      f: scm.GIT.GetOldContents(self._root, f, self._branch)
      for _, f in scm.GIT.CaptureStatus(self._root, self._branch)
      if os.path.basename(f) == 'OWNERS'
    })

  def ListOwnersForFile(self, _project, _branch, path):
    return sorted(self._db.all_possible_owners([path], None))

  def GetChangeApprovalStatus(self, change_id):
    data = gerrit_util.GetChange(
        self._host, change_id,
        ['DETAILED_ACCOUNTS', 'DETAILED_LABELS', 'CURRENT_FILES',
         'CURRENT_REVISION'])

    reviewers = [r['email'] for r in data['reviewers']['REVIEWER']]

    # Get reviewers that have approved this change
    label = change['labels']['Code-Review']
    max_value = max(int(v) for v in label['values'])
    approvers = [v['email'] for v in label['all'] if v['value'] == max_value]

    files = data['revisions'][data['current_revision']]['files']

    self._db.load_data_needed_for(files)

    status = {}
    for f in files:
      if self._db.is_covered_by(f, approvers):
        status[f] = APPROVED
      elif self._db.is_covered_by(f, reviewers):
        status[f] = PENDING
      else:
        status[f] = INSUFFICIENT_REVIEWERS
    return status
