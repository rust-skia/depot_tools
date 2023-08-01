#!/usr/bin/env vpython3
"""Tests for split_cl."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import split_cl


class SplitClTest(unittest.TestCase):
  def testAddUploadedByGitClSplitToDescription(self):
    description = """Convert use of X to Y in $directory

<add some background about this conversion for the reviewers>

"""
    footers = 'Bug: 12345'

    added_line = 'This CL was uploaded by git cl split.'

    # Description without footers
    self.assertEqual(split_cl.AddUploadedByGitClSplitToDescription(description),
                     description + added_line)
    # Description with footers
    self.assertEqual(
        split_cl.AddUploadedByGitClSplitToDescription(description + footers),
        description + added_line + '\n\n' + footers)

  def testFormatDescriptionOrComment(self):
    description = "Converted use of X to Y in $directory."

    # One directory
    self.assertEqual(split_cl.FormatDescriptionOrComment(description, ["foo"]),
                     "Converted use of X to Y in /foo.")

    # Many directories
    self.assertEqual(
        split_cl.FormatDescriptionOrComment(description, ["foo", "bar"]),
        "Converted use of X to Y in ['/foo', '/bar'].")

  def GetDirectoryBaseName(self, file_path):
    return os.path.basename(os.path.dirname(file_path))

  def MockSuggestOwners(self, paths, exclude=None):
    if not paths:
      return ["superowner"]
    return self.GetDirectoryBaseName(paths[0]).split(",")

  def MockIsFile(self, file_path):
    if os.path.basename(file_path) == "OWNERS":
      return "owner" in self.GetDirectoryBaseName(file_path)

    return True

  @mock.patch("os.path.isfile")
  def testSelectReviewersForFiles(self, mock_is_file):
    mock_is_file.side_effect = self.MockIsFile

    owners_client = mock.Mock(SuggestOwners=self.MockSuggestOwners,
                              EVERYONE="*")
    cl = mock.Mock(owners_client=owners_client)

    files = [("M", "foo/owner1,owner2/a.txt"), ("M", "foo/owner1,owner2/b.txt"),
             ("M", "bar/owner1,owner2/c.txt"), ("M", "bax/owner2/d.txt"),
             ("M", "baz/owner3/e.txt")]

    files_split_by_reviewers = split_cl.SelectReviewersForFiles(
        cl, "author", files, 0)

    self.assertEqual(3, len(files_split_by_reviewers.keys()))
    info1 = files_split_by_reviewers[tuple(["owner1", "owner2"])]
    self.assertEqual(info1.files, [("M", "foo/owner1,owner2/a.txt"),
                                   ("M", "foo/owner1,owner2/b.txt"),
                                   ("M", "bar/owner1,owner2/c.txt")])
    self.assertEqual(info1.owners_directories,
                     ["foo/owner1,owner2", "bar/owner1,owner2"])
    info2 = files_split_by_reviewers[tuple(["owner2"])]
    self.assertEqual(info2.files, [("M", "bax/owner2/d.txt")])
    self.assertEqual(info2.owners_directories, ["bax/owner2"])
    info3 = files_split_by_reviewers[tuple(["owner3"])]
    self.assertEqual(info3.files, [("M", "baz/owner3/e.txt")])
    self.assertEqual(info3.owners_directories, ["baz/owner3"])


if __name__ == '__main__':
  unittest.main()
