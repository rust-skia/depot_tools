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
import owners_client

from testing_support import filesystem_mock


alice = 'alice@example.com'
bob = 'bob@example.com'
chris = 'chris@example.com'
dave = 'dave@example.com'
emily = 'emily@example.com'


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


class TestClient(owners_client.OwnersClient):
  def __init__(self, host, owners_by_path):
    super(TestClient, self).__init__(host)
    self.owners_by_path = owners_by_path

  def ListOwnersForFile(self, _project, _branch, path):
    return self.owners_by_path[path]


class OwnersClientTest(unittest.TestCase):
  def setUp(self):
    self.owners = {}
    self.client = TestClient('host', self.owners)

  def testGetFilesApprovalStatus(self):
    self.client.owners_by_path = {
      'approved': ['approver@example.com'],
      'pending': ['reviewer@example.com'],
      'insufficient': ['insufficient@example.com'],
    }
    status = self.client.GetFilesApprovalStatus(
        'project', 'branch',
        ['approved', 'pending', 'insufficient'],
        ['approver@example.com'], ['reviewer@example.com'])
    self.assertEqual(
        status,
        {
            'approved': owners_client.APPROVED,
            'pending': owners_client.PENDING,
            'insufficient': owners_client.INSUFFICIENT_REVIEWERS,
        })

  def test_owner_combinations(self):
    owners = [alice, bob, chris, dave, emily]
    self.assertEqual(
        list(owners_client._owner_combinations(owners, 2)),
        [(bob, alice),
         (chris, alice),
         (chris, bob),
         (dave, alice),
         (dave, bob),
         (dave, chris),
         (emily, alice),
         (emily, bob),
         (emily, chris),
         (emily, dave)])

  def testSuggestOwners(self):
    self.client.owners_by_path = {'a': [alice]}
    self.assertEqual(
        self.client.SuggestOwners('project', 'branch', ['a']),
        [alice])

    self.client.owners_by_path = {'abcd': [alice, bob, chris, dave]}
    self.assertEqual(
        self.client.SuggestOwners('project', 'branch', ['abcd']),
        (bob, alice))

    self.client.owners_by_path = {
        'ae': [alice, emily],
        'be': [bob, emily],
        'ce': [chris, emily],
        'de': [dave, emily],
    }
    self.assertEqual(
        self.client.SuggestOwners(
            'project', 'branch', ['ae', 'be', 'ce', 'de']),
        (emily, bob))

    self.client.owners_by_path = {
        'ad': [alice, dave],
        'cad': [chris, alice, dave],
        'ead': [emily, alice, dave],
        'bd': [bob, dave],
    }
    self.assertEqual(
        self.client.SuggestOwners(
            'project', 'branch', ['ad', 'cad', 'ead', 'bd']),
        (bob, alice))

    self.client.owners_by_path = {
        'a': [alice],
        'b': [bob],
        'c': [chris],
        'ad': [alice, dave],
    }
    self.assertEqual(
        self.client.SuggestOwners(
            'project', 'branch', ['a', 'b', 'c', 'ad']),
        (alice, chris, bob))

    self.client.owners_by_path = {
        'abc': [alice, bob, chris],
        'acb': [alice, chris, bob],
        'bac': [bob, alice, chris],
        'bca': [bob, chris, alice],
        'cab': [chris, alice, bob],
        'cba': [chris, bob, alice]
    }
    self.assertEqual(
        self.client.SuggestOwners(
            'project', 'branch',
            ['abc', 'acb', 'bac', 'bca', 'cab', 'cba']),
        (chris, bob))


if __name__ == '__main__':
  unittest.main()
