# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import unittest

if sys.version_info.major == 2:
  import mock
else:
  from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gerrit_util
import owners
import owners_client

from testing_support import filesystem_mock


def _get_change():
  return {
    "labels": {
      "Code-Review": {
        "all": [
          {
            "value": 1,
            "email": "approver@example.com",
          }
        ],
        "values": {
          "-1": "Don't submit as-is",
          " 0": "No score",
          "+1": "Looks good to me"
        },
      },
    },
    "reviewers": {
      "REVIEWER": [
        {"email": "approver@example.com"},
        {"email": "reviewer@example.com"},
      ],
    },
    "current_revision": "cb90826d03533d6c4e1f0e974ebcbfd7a6f42406",
    "revisions": {
      "cb90826d03533d6c4e1f0e974ebcbfd7a6f42406": {
        "files": {
          "approved.cc": {},
          "reviewed.h": {},
          "bar/insufficient.py": {},
        },
      },
    },
  }



class DepotToolsClientTest(unittest.TestCase):
  def setUp(self):
    self.repo = filesystem_mock.MockFileSystem(files={
        '/OWNERS': '\n'.join([
            'per-file approved.cc=approver@example.com',
            'per-file reviewed.h=reviewer@example.com',
            'missing@example.com',
        ]),
        '/approved.cc': '',
        '/reviewed.h': '',
        '/bar/insufficient_reviewers.py': '',
        '/bar/everyone/OWNERS': '*',
        '/bar/everyone/foo.txt': '',
    })
    self.root = '/'
    self.fopen = self.repo.open_for_reading
    mock.patch(
        'owners_client.DepotToolsClient._GetOriginalOwnersFiles',
        return_value={}).start()
    self.addCleanup(mock.patch.stopall)
    self.client = owners_client.DepotToolsClient(
        'host', '/', 'branch', self.fopen, self.repo)

  def testListOwners(self):
    self.assertEquals(
        ['*', 'missing@example.com'],
        self.client.ListOwnersForFile(
            'project', 'branch', 'bar/everyone/foo.txt'))

  @mock.patch('gerrit_util.GetChange', return_value=_get_change())
  def testGetChangeApprovalStatus(self, _mock):
    self.assertEquals(
        {
            'approved.cc': owners_client.APPROVED,
            'reviewed.h': owners_client.PENDING,
            'bar/insufficient.py': owners_client.INSUFFICIENT_REVIEWERS,
        },
        self.client.GetChangeApprovalStatus('changeid'))

  @mock.patch('gerrit_util.GetChange', return_value=_get_change())
  def testValidateOwnersConfig_OK(self, get_change_mock):
    self.client.ValidateOwnersConfig('changeid')

  @mock.patch('gerrit_util.GetChange', return_value=_get_change())
  def testValidateOwnersConfig_Invalid(self, get_change_mock):
    change = get_change_mock()
    change['revisions'][change['current_revision']]['files'] = {'/OWNERS': {}}
    self.repo.files['/OWNERS'] = '\n'.join([
        'foo@example.com',
        'invalid directive',
    ])
    with self.assertRaises(owners_client.InvalidOwnersConfig):
      self.client.ValidateOwnersConfig('changeid')


if __name__ == '__main__':
  unittest.main()
