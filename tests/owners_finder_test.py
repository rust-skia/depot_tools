#!/usr/bin/env vpython3
# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for owners_finder.py."""

import os
import sys
import unittest

if sys.version_info.major == 2:
  import mock
else:
  from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_support import filesystem_mock

import owners_finder
import owners_client


ben = 'ben@example.com'
brett = 'brett@example.com'
darin = 'darin@example.com'
jochen = 'jochen@example.com'
john = 'john@example.com'
ken = 'ken@example.com'
peter = 'peter@example.com'
tom = 'tom@example.com'
nonowner = 'nonowner@example.com'


def _get_score_owners_darin_variant():
  return [brett, darin, john, peter, ken, ben, tom]


def _get_score_owners_john_variant():
  return [brett, john, darin, peter, ken, ben, tom]


def owners_file(*email_addresses, **kwargs):
  s = ''
  if kwargs.get('comment'):
    s += '# %s\n' % kwargs.get('comment')
  if kwargs.get('noparent'):
    s += 'set noparent\n'
  return s + '\n'.join(email_addresses) + '\n'


def test_repo():
  return filesystem_mock.MockFileSystem(files={
    '/DEPS': '',
    '/OWNERS': owners_file(ken, peter, tom,
                           comment='OWNERS_STATUS = build/OWNERS.status'),
    '/build/OWNERS.status': '%s: bar' % jochen,
    '/base/vlog.h': '',
    '/chrome/OWNERS': owners_file(ben, brett),
    '/chrome/browser/OWNERS': owners_file(brett),
    '/chrome/browser/defaults.h': '',
    '/chrome/gpu/OWNERS': owners_file(ken),
    '/chrome/gpu/gpu_channel.h': '',
    '/chrome/renderer/OWNERS': owners_file(peter),
    '/chrome/renderer/gpu/gpu_channel_host.h': '',
    '/chrome/renderer/safe_browsing/scorer.h': '',
    '/content/OWNERS': owners_file(john, darin, comment='foo', noparent=True),
    '/content/content.gyp': '',
    '/content/bar/foo.cc': '',
    '/content/baz/OWNERS': owners_file(brett),
    '/content/baz/froboz.h': '',
    '/content/baz/ugly.cc': '',
    '/content/baz/ugly.h': '',
    '/content/common/OWNERS': owners_file(jochen),
    '/content/common/common.cc': '',
    '/content/foo/OWNERS': owners_file(jochen, comment='foo'),
    '/content/foo/foo.cc': '',
    '/content/views/OWNERS': owners_file(ben, john,
                                         owners_client.OwnersClient.EVERYONE,
                                         noparent=True),
    '/content/views/pie.h': '',
  })


class OutputInterceptedOwnersFinder(owners_finder.OwnersFinder):
  def __init__(self, files, local_root, author, reviewers,
               fopen, os_path, disable_color=False):
    super(OutputInterceptedOwnersFinder, self).__init__(
      files, local_root, author, reviewers, fopen, os_path,
      disable_color=disable_color)
    self.output = []
    self.indentation_stack = []

  def resetText(self):
    self.output = []
    self.indentation_stack = []

  def indent(self):
    self.indentation_stack.append(self.output)
    self.output = []

  def unindent(self):
    block = self.output
    self.output = self.indentation_stack.pop()
    self.output.append(block)

  def writeln(self, text=''):
    self.output.append(text)


class _BaseTestCase(unittest.TestCase):
  default_files = [
    'base/vlog.h',
    'chrome/browser/defaults.h',
    'chrome/gpu/gpu_channel.h',
    'chrome/renderer/gpu/gpu_channel_host.h',
    'chrome/renderer/safe_browsing/scorer.h',
    'content/content.gyp',
    'content/bar/foo.cc',
    'content/baz/ugly.cc',
    'content/baz/ugly.h',
    'content/views/pie.h'
  ]

  def setUp(self):
    self.repo = test_repo()
    self.root = '/'
    self.fopen = self.repo.open_for_reading
    mock.patch('owners_client.DepotToolsClient._GetOriginalOwnersFiles',
      return_value={}).start()
    self.addCleanup(mock.patch.stopall)

  def ownersFinder(self, files, author=nonowner, reviewers=None):
    reviewers = reviewers or []
    finder = OutputInterceptedOwnersFinder(files,
                                           self.root,
                                           author,
                                           reviewers,
                                           fopen=self.fopen,
                                           os_path=self.repo,
                                           disable_color=True)
    return finder

  def defaultFinder(self):
    return self.ownersFinder(self.default_files)


class OwnersFinderTests(_BaseTestCase):
  def test_constructor(self):
    self.assertNotEqual(self.defaultFinder(), None)

  def test_skip_files_owned_by_reviewers(self):
    files = [
        'chrome/browser/defaults.h',  # owned by brett
        'content/bar/foo.cc',         # not owned by brett
    ]
    finder = self.ownersFinder(files, reviewers=[brett])
    self.assertEqual(finder.unreviewed_files, {'content/bar/foo.cc'})

  def test_skip_files_owned_by_author(self):
    files = [
        'chrome/browser/defaults.h',  # owned by brett
        'content/bar/foo.cc',         # not owned by brett
    ]
    finder = self.ownersFinder(files, author=brett)
    self.assertEqual(finder.unreviewed_files, {'content/bar/foo.cc'})

  def test_native_path_sep(self):
    # Create a path with backslashes on Windows to make sure these are handled.
    # This test is a harmless duplicate on other platforms.
    native_slashes_path = 'chrome/browser/defaults.h'.replace('/', os.sep)
    files = [
        native_slashes_path,          # owned by brett
        'content/bar/foo.cc',         # not owned by brett
    ]
    finder = self.ownersFinder(files, reviewers=[brett])
    self.assertEqual(finder.unreviewed_files, {'content/bar/foo.cc'})

  def test_reset(self):
    mock.patch('owners_client.DepotToolsClient.ScoreOwners',
      side_effect=[
        _get_score_owners_darin_variant(),
        _get_score_owners_darin_variant(),
        _get_score_owners_darin_variant()
      ]).start()

    finder = self.defaultFinder()
    for _ in range(2):
      expected = [brett, darin, john, peter, ken, ben, tom]
      self.assertEqual(finder.owners_queue, expected)
      self.assertEqual(finder.unreviewed_files, {
          'base/vlog.h',
          'chrome/browser/defaults.h',
          'chrome/gpu/gpu_channel.h',
          'chrome/renderer/gpu/gpu_channel_host.h',
          'chrome/renderer/safe_browsing/scorer.h',
          'content/content.gyp',
          'content/bar/foo.cc',
          'content/baz/ugly.cc',
          'content/baz/ugly.h'
      })
      self.assertEqual(finder.selected_owners, set())
      self.assertEqual(finder.deselected_owners, set())
      self.assertEqual(finder.reviewed_by, {})
      self.assertEqual(finder.output, [])

      finder.select_owner(john)
      finder.reset()
      finder.resetText()

  def test_select(self):
    mock.patch('owners_client.DepotToolsClient.ScoreOwners',
      side_effect=[
        _get_score_owners_darin_variant(),
        _get_score_owners_john_variant(),
        _get_score_owners_darin_variant()
      ]).start()

    finder = self.defaultFinder()
    finder.select_owner(john)
    self.assertEqual(finder.owners_queue, [brett, peter, ken, ben, tom])
    self.assertEqual(finder.selected_owners, {john})
    self.assertEqual(finder.deselected_owners, {darin})
    self.assertEqual(finder.reviewed_by, {'content/bar/foo.cc': john,
                                          'content/baz/ugly.cc': john,
                                          'content/baz/ugly.h': john,
                                          'content/content.gyp': john})
    self.assertEqual(finder.output,
                     ['Selected: ' + john, 'Deselected: ' + darin])

    finder = self.defaultFinder()
    finder.select_owner(darin)
    self.assertEqual(finder.owners_queue, [brett, peter, ken, ben, tom])
    self.assertEqual(finder.selected_owners, {darin})
    self.assertEqual(finder.deselected_owners, {john})
    self.assertEqual(finder.reviewed_by, {'content/bar/foo.cc': darin,
                                          'content/baz/ugly.cc': darin,
                                          'content/baz/ugly.h': darin,
                                          'content/content.gyp': darin})
    self.assertEqual(finder.output,
                     ['Selected: ' + darin, 'Deselected: ' + john])

    finder = self.defaultFinder()
    finder.select_owner(brett)
    expected = [darin, john, peter, ken, tom]
    self.assertEqual(finder.owners_queue, expected)
    self.assertEqual(finder.selected_owners, {brett})
    self.assertEqual(finder.deselected_owners, {ben})
    self.assertEqual(finder.reviewed_by,
                     {'chrome/browser/defaults.h': brett,
                      'chrome/gpu/gpu_channel.h': brett,
                      'chrome/renderer/gpu/gpu_channel_host.h': brett,
                      'chrome/renderer/safe_browsing/scorer.h': brett,
                      'content/baz/ugly.cc': brett,
                      'content/baz/ugly.h': brett})
    self.assertEqual(finder.output,
                     ['Selected: ' + brett, 'Deselected: ' + ben])

  def test_deselect(self):
    mock.patch('owners_client.DepotToolsClient.ScoreOwners',
      return_value=_get_score_owners_darin_variant()).start()

    finder = self.defaultFinder()
    finder.deselect_owner(john)
    self.assertEqual(finder.owners_queue, [brett, peter, ken, ben, tom])
    self.assertEqual(finder.selected_owners, {darin})
    self.assertEqual(finder.deselected_owners, {john})
    self.assertEqual(finder.reviewed_by, {'content/bar/foo.cc': darin,
                                          'content/baz/ugly.cc': darin,
                                          'content/baz/ugly.h': darin,
                                          'content/content.gyp': darin})
    self.assertEqual(finder.output,
                     ['Deselected: ' + john, 'Selected: ' + darin])

  def test_print_file_info(self):
    finder = self.defaultFinder()
    finder.print_file_info('chrome/browser/defaults.h')
    self.assertEqual(finder.output, ['chrome/browser/defaults.h [5]'])
    finder.resetText()

    finder.print_file_info('chrome/renderer/gpu/gpu_channel_host.h')
    self.assertEqual(finder.output,
                     ['chrome/renderer/gpu/gpu_channel_host.h [5]'])

  def test_print_file_info_detailed(self):
    finder = self.defaultFinder()
    finder.print_file_info_detailed('chrome/browser/defaults.h')
    self.assertEqual(finder.output,
                     ['chrome/browser/defaults.h',
                       [ben, brett, ken, peter, tom]])
    finder.resetText()

    finder.print_file_info_detailed('chrome/renderer/gpu/gpu_channel_host.h')
    self.assertEqual(finder.output,
                     ['chrome/renderer/gpu/gpu_channel_host.h',
                       [ben, brett, ken, peter, tom]])


if __name__ == '__main__':
  unittest.main()
