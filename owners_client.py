# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import itertools
import os
import random

import gerrit_util
import git_common
import owners as owners_db
import scm


APPROVED = 'APPROVED'
PENDING = 'PENDING'
INSUFFICIENT_REVIEWERS = 'INSUFFICIENT_REVIEWERS'


def _owner_combinations(owners, num_owners):
  """Iterate owners combinations by decrasing score.

  The score of an owner is its position on the owners list.
  The score of a set of owners is the maximum score of all owners on the set.

  Returns all combinations of up to `num_owners` sorted by decreasing score:
    _owner_combinations(['0', '1', '2', '3'], 2) == [
        # score 1
        ('1', '0'),
        # score 2
        ('2', '0'),
        ('2', '1'),
        # score 3
        ('3', '0'),
        ('3', '1'),
        ('3', '2'),
    ]
  """
  return reversed(list(itertools.combinations(reversed(owners), num_owners)))


class InvalidOwnersConfig(Exception):
  pass


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
    """List all owners for a file.

    The returned list is sorted so that better owners appear first.
    """
    raise Exception('Not implemented')

  def BatchListOwners(self, project, branch, paths):
    """Returns a dictionary {path: [owners]}."""
    with git_common.ScopedPool(kind='threads') as pool:
      return dict(pool.imap_unordered(
          lambda p: (p, self.ListOwnersForFile(project, branch, p)), paths))

  def GetChangeApprovalStatus(self, change_id):
    """Check the approval status for the latest revision_id in a change.

    Returns a map of path to approval status, where the status can be one of:
    - APPROVED: An owner of the file has reviewed the change.
    - PENDING:  An owner of the file has been added as a reviewer, but no owner
      has approved.
    - INSUFFICIENT_REVIEWERS: No owner of the file has been added as a reviewer.
    """
    raise Exception('Not implemented')

  def ValidateOwnersConfig(self, change_id):
    """Check if the owners configuration in a change is valid."""
    raise Exception('Not implemented')

  def GetFilesApprovalStatus(
      self, project, branch, paths, approvers, reviewers):
    """Check the approval status for the given paths.

    Utility method to check for approval status when a change has not yet been
    created, given reviewers and approvers.

    See GetChangeApprovalStatus for description of the returned value.
    """
    approvers = set(approvers)
    reviewers = set(reviewers)
    status = {}
    for path in paths:
      path_owners = set(self.ListOwnersForFile(project, branch, path))
      if path_owners.intersection(approvers):
        status[path] = APPROVED
      elif path_owners.intersection(reviewers):
        status[path] = PENDING
      else:
        status[path] = INSUFFICIENT_REVIEWERS
    return status

  def SuggestOwners(self, project, branch, paths):
    """Suggest a set of owners for the given paths."""
    paths_by_owner = {}
    score_by_owner = {}
    for path in paths:
      owners = self.ListOwnersForFile(project, branch, path)
      for i, owner in enumerate(owners):
        paths_by_owner.setdefault(owner, set()).add(path)
        # Gerrit API lists owners of a path sorted by an internal score, so
        # owners that appear first should be prefered.
        # We define the score of an owner to be their minimum position in all
        # paths.
        score_by_owner[owner] = min(i, score_by_owner.get(owner, i))

    # Sort owners by their score.
    owners = sorted(score_by_owner, key=lambda o: score_by_owner[o])

    # Select the minimum number of owners that can approve all paths.
    # We start at 2 to avoid sending all changes that require multiple reviewers
    # to top-level owners.
    if len(owners) < 2:
      return owners

    for num_owners in range(2, len(owners)):
      # Iterate all combinations of `num_owners` by decreasing score, and select
      # the first one that covers all paths.
      for selected in _owner_combinations(owners, num_owners):
        covered = set.union(*(paths_by_owner[o] for o in selected))
        if len(covered) == len(paths):
          return selected


class DepotToolsClient(OwnersClient):
  """Implement OwnersClient using owners.py Database."""
  def __init__(self, host, root, branch, fopen=open, os_path=os.path):
    super(DepotToolsClient, self).__init__(host)
    self._root = root
    self._fopen = fopen
    self._os_path = os_path
    self._branch = branch
    self._db = owners_db.Database(root, fopen, os_path)
    self._db.override_files = self._GetOriginalOwnersFiles()

  def _GetOriginalOwnersFiles(self):
    return {
      f: scm.GIT.GetOldContents(self._root, f, self._branch).splitlines()
      for _, f in scm.GIT.CaptureStatus(self._root, self._branch)
      if os.path.basename(f) == 'OWNERS'
    }

  def ListOwnersForFile(self, _project, _branch, path):
    # all_possible_owners returns a dict {owner: [(path, distance)]}. We want to
    # return a list of owners sorted by increasing distance.
    distance_by_owner = self._db.all_possible_owners([path], None)
    # We add a small random number to the distance, so that owners at the same
    # distance are returned in random order to avoid overloading those who would
    # appear first.
    return sorted(
        distance_by_owner,
        key=lambda o: distance_by_owner[o][0][1] + random.random())

  def GetChangeApprovalStatus(self, change_id):
    data = gerrit_util.GetChange(
        self._host, change_id,
        ['DETAILED_ACCOUNTS', 'DETAILED_LABELS', 'CURRENT_FILES',
         'CURRENT_REVISION'])

    reviewers = [r['email'] for r in data['reviewers']['REVIEWER']]

    # Get reviewers that have approved this change
    label = data['labels']['Code-Review']
    max_value = max(int(v) for v in label['values'])
    approvers = [v['email'] for v in label['all'] if v['value'] == max_value]

    files = data['revisions'][data['current_revision']]['files']
    return self.GetFilesApprovalStatus(None, None, files, approvers, reviewers)

  def ValidateOwnersConfig(self, change_id):
    data = gerrit_util.GetChange(
        self._host, change_id,
        ['DETAILED_ACCOUNTS', 'DETAILED_LABELS', 'CURRENT_FILES',
         'CURRENT_REVISION'])

    files = data['revisions'][data['current_revision']]['files']

    db = owners_db.Database(self._root, self._fopen, self._os_path)
    try:
      db.load_data_needed_for(
          [f for f in files if os.path.basename(f) == 'OWNERS'])
    except Exception as e:
      raise InvalidOwnersConfig('Error parsing OWNERS files:\n%s' % e)


class GerritClient(OwnersClient):
  """Implement OwnersClient using OWNERS REST API."""
  def __init__(self, host):
    super(GerritClient, self).__init__(host)

  def ListOwnersForFile(self, project, branch, path):
    # GetOwnersForFile returns a list of account details sorted by order of
    # best reviewer for path. If code owners have the same score, the order is
    # random.
    data = gerrit_util.GetOwnersForFile(self._host, project, branch, path)
    return [d['account']['email'] for d in data]
