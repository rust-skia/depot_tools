# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re

from . import scm, utils

# expectation is that depot_too
import git_footers


def RightHandSideLinesImpl(affected_files):
  """Implements RightHandSideLines for InputApi and GclChange."""
  for af in affected_files:
    lines = af.ChangedContents()
    for line in lines:
      yield (af, line[0], line[1])


class _DiffCache(object):
  """Caches diffs retrieved from a particular SCM."""
  def __init__(self, upstream=None):
    """Stores the upstream revision against which all diffs will be computed."""
    self._upstream = upstream

  def GetDiff(self, path, local_root):
    """Get the diff for a particular path."""
    raise NotImplementedError()

  def GetOldContents(self, path, local_root):
    """Get the old version for a particular path."""
    raise NotImplementedError()


class _GitDiffCache(_DiffCache):
  """DiffCache implementation for git; gets all file diffs at once."""
  def __init__(self, upstream):
    super(_GitDiffCache, self).__init__(upstream=upstream)
    self._diffs_by_file = None

  def GetDiff(self, path, local_root):
    # Compare against None to distinguish between None and an initialized but
    # empty dictionary.
    if self._diffs_by_file == None:
      # Compute a single diff for all files and parse the output; should
      # with git this is much faster than computing one diff for each file.
      diffs = {}

      # Don't specify any filenames below, because there are command line length
      # limits on some platforms and GenerateDiff would fail.
      unified_diff = scm.GIT.GenerateDiff(local_root,
                                          files=[],
                                          full_move=True,
                                          branch=self._upstream)

      # This regex matches the path twice, separated by a space. Note that
      # filename itself may contain spaces.
      file_marker = re.compile('^diff --git (?P<filename>.*) (?P=filename)$')
      current_diff = []
      keep_line_endings = True
      for x in unified_diff.splitlines(keep_line_endings):
        match = file_marker.match(x)
        if match:
          # Marks the start of a new per-file section.
          diffs[match.group('filename')] = current_diff = [x]
        elif x.startswith('diff --git'):
          raise PresubmitFailure('Unexpected diff line: %s' % x)
        else:
          current_diff.append(x)

      self._diffs_by_file = dict(
          (utils.normpath(path), ''.join(diff)) for path, diff in diffs.items())

    if path not in self._diffs_by_file:
      # SCM didn't have any diff on this file. It could be that the file was not
      # modified at all (e.g. user used --all flag in git cl presubmit).
      # Intead of failing, return empty string.
      # See: https://crbug.com/808346.
      return ''

    return self._diffs_by_file[path]

  def GetOldContents(self, path, local_root):
    return scm.GIT.GetOldContents(local_root, path, branch=self._upstream)


class AffectedFile(object):
  """Representation of a file in a change."""

  DIFF_CACHE = _DiffCache

  # Method could be a function
  # pylint: disable=no-self-use
  def __init__(self, path, action, repository_root, diff_cache):
    self._path = path
    self._action = action
    self._local_root = repository_root
    self._is_directory = None
    self._cached_changed_contents = None
    self._cached_new_contents = None
    self._diff_cache = diff_cache
    logging.debug('%s(%s)', self.__class__.__name__, self._path)

  def LocalPath(self):
    """Returns the path of this file on the local disk relative to client root.

    This should be used for error messages but not for accessing files,
    because presubmit checks are run with CWD=PresubmitLocalPath() (which is
    often != client root).
    """
    return utils.normpath(self._path)

  def AbsoluteLocalPath(self):
    """Returns the absolute path of this file on the local disk.
    """
    return os.path.abspath(os.path.join(self._local_root, self.LocalPath()))

  def Action(self):
    """Returns the action on this opened file, e.g. A, M, D, etc."""
    return self._action

  def IsTestableFile(self):
    """Returns True if the file is a text file and not a binary file.

    Deleted files are not text file."""
    raise NotImplementedError()  # Implement when needed

  def IsTextFile(self):
    """An alias to IsTestableFile for backwards compatibility."""
    return self.IsTestableFile()

  def OldContents(self):
    """Returns an iterator over the lines in the old version of file.

    The old version is the file before any modifications in the user's
    workspace, i.e. the 'left hand side'.

    Contents will be empty if the file is a directory or does not exist.
    Note: The carriage returns (LF or CR) are stripped off.
    """
    return self._diff_cache.GetOldContents(self.LocalPath(),
                                           self._local_root).splitlines()

  def NewContents(self):
    """Returns an iterator over the lines in the new version of file.

    The new version is the file in the user's workspace, i.e. the 'right hand
    side'.

    Contents will be empty if the file is a directory or does not exist.
    Note: The carriage returns (LF or CR) are stripped off.
    """
    if self._cached_new_contents is None:
      self._cached_new_contents = []
      try:
        self._cached_new_contents = utils.FileRead(self.AbsoluteLocalPath(),
                                                   'rU').splitlines()
      except IOError:
        pass  # File not found?  That's fine; maybe it was deleted.
      except UnicodeDecodeError as e:
        # log the filename since we're probably trying to read a binary
        # file, and shouldn't be.
        print('Error reading %s: %s' % (self.AbsoluteLocalPath(), e))
        raise

    return self._cached_new_contents[:]

  def ChangedContents(self, keeplinebreaks=False):
    """Returns a list of tuples (line number, line text) of all new lines.

     This relies on the scm diff output describing each changed code section
     with a line of the form

     ^@@ <old line num>,<old size> <new line num>,<new size> @@$
    """
    # Don't return cached results when line breaks are requested.
    if not keeplinebreaks and self._cached_changed_contents is not None:
      return self._cached_changed_contents[:]
    result = []
    line_num = 0

    # The keeplinebreaks parameter to splitlines must be True or else the
    # CheckForWindowsLineEndings presubmit will be a NOP.
    for line in self.GenerateScmDiff().splitlines(keeplinebreaks):
      m = re.match(r'^@@ [0-9\,\+\-]+ \+([0-9]+)\,[0-9]+ @@', line)
      if m:
        line_num = int(m.groups(1)[0])
        continue
      if line.startswith('+') and not line.startswith('++'):
        result.append((line_num, line[1:]))
      if not line.startswith('-'):
        line_num += 1
    # Don't cache results with line breaks.
    if keeplinebreaks:
      return result
    self._cached_changed_contents = result
    return self._cached_changed_contents[:]

  def __str__(self):
    return self.LocalPath()

  def GenerateScmDiff(self):
    return self._diff_cache.GetDiff(self.LocalPath(), self._local_root)


class GitAffectedFile(AffectedFile):
  """Representation of a file in a change out of a git checkout."""
  # Method 'NNN' is abstract in class 'NNN' but is not overridden
  # pylint: disable=abstract-method

  DIFF_CACHE = _GitDiffCache

  def __init__(self, *args, **kwargs):
    AffectedFile.__init__(self, *args, **kwargs)
    self._server_path = None
    self._is_testable_file = None

  def IsTestableFile(self):
    if self._is_testable_file is None:
      if self.Action() == 'D':
        # A deleted file is not testable.
        self._is_testable_file = False
      else:
        self._is_testable_file = os.path.isfile(self.AbsoluteLocalPath())
    return self._is_testable_file


class Change(object):
  """Describe a change.

  Used directly by the presubmit scripts to query the current change being
  tested.

  Instance members:
    tags: Dictionary of KEY=VALUE pairs found in the change description.
    self.KEY: equivalent to tags['KEY']
  """

  _AFFECTED_FILES = AffectedFile

  # Matches key/value (or 'tag') lines in changelist descriptions.
  TAG_LINE_RE = re.compile(
      '^[ \t]*(?P<key>[A-Z][A-Z_0-9]*)[ \t]*=[ \t]*(?P<value>.*?)[ \t]*$')
  scm = ''

  def __init__(self,
               name,
               description,
               local_root,
               files,
               issue,
               patchset,
               author,
               upstream=None):
    if files is None:
      files = []
    self._name = name
    # Convert root into an absolute path.
    self._local_root = os.path.abspath(local_root)
    self._upstream = upstream
    self.issue = issue
    self.patchset = patchset
    self.author_email = author

    self._full_description = ''
    self.tags = {}
    self._description_without_tags = ''
    self.SetDescriptionText(description)

    assert all(
        (isinstance(f, (list, tuple)) and len(f) == 2) for f in files), files

    diff_cache = self._AFFECTED_FILES.DIFF_CACHE(self._upstream)
    self._affected_files = [
        self._AFFECTED_FILES(path, action.strip(), self._local_root, diff_cache)
        for action, path in files
    ]

  def UpstreamBranch(self):
    """Returns the upstream branch for the change."""
    return self._upstream

  def Name(self):
    """Returns the change name."""
    return self._name

  def DescriptionText(self):
    """Returns the user-entered changelist description, minus tags.

    Any line in the user-provided description starting with e.g. 'FOO='
    (whitespace permitted before and around) is considered a tag line.  Such
    lines are stripped out of the description this function returns.
    """
    return self._description_without_tags

  def FullDescriptionText(self):
    """Returns the complete changelist description including tags."""
    return self._full_description

  def SetDescriptionText(self, description):
    """Sets the full description text (including tags) to |description|.

    Also updates the list of tags."""
    self._full_description = description

    # From the description text, build up a dictionary of key/value pairs
    # plus the description minus all key/value or 'tag' lines.
    description_without_tags = []
    self.tags = {}
    for line in self._full_description.splitlines():
      m = self.TAG_LINE_RE.match(line)
      if m:
        self.tags[m.group('key')] = m.group('value')
      else:
        description_without_tags.append(line)

    # Change back to text and remove whitespace at end.
    self._description_without_tags = (
        '\n'.join(description_without_tags).rstrip())

  def AddDescriptionFooter(self, key, value):
    """Adds the given footer to the change description.

    Args:
      key: A string with the key for the git footer. It must conform to
        the git footers format (i.e. 'List-Of-Tokens') and will be case
        normalized so that each token is title-cased.
      value: A string with the value for the git footer.
    """
    description = git_footers.add_footer(self.FullDescriptionText(),
                                         git_footers.normalize_name(key), value)
    self.SetDescriptionText(description)

  def RepositoryRoot(self):
    """Returns the repository (checkout) root directory for this change,
    as an absolute path.
    """
    return self._local_root

  def __getattr__(self, attr):
    """Return tags directly as attributes on the object."""
    if not re.match(r'^[A-Z_]*$', attr):
      raise AttributeError(self, attr)
    return self.tags.get(attr)

  def GitFootersFromDescription(self):
    """Return the git footers present in the description.

    Returns:
      footers: A dict of {footer: [values]} containing a multimap of the footers
        in the change description.
    """
    return git_footers.parse_footers(self.FullDescriptionText())

  def BugsFromDescription(self):
    """Returns all bugs referenced in the commit description."""
    bug_tags = ['BUG', 'FIXED']

    tags = []
    for tag in bug_tags:
      values = self.tags.get(tag)
      if values:
        tags += [value.strip() for value in values.split(',')]

    footers = []
    parsed = self.GitFootersFromDescription()
    unsplit_footers = parsed.get('Bug', []) + parsed.get('Fixed', [])
    for unsplit_footer in unsplit_footers:
      footers += [b.strip() for b in unsplit_footer.split(',')]
    return sorted(set(tags + footers))

  def ReviewersFromDescription(self):
    """Returns all reviewers listed in the commit description."""
    # We don't support a 'R:' git-footer for reviewers; that is in metadata.
    tags = [r.strip() for r in self.tags.get('R', '').split(',') if r.strip()]
    return sorted(set(tags))

  def TBRsFromDescription(self):
    """Returns all TBR reviewers listed in the commit description."""
    tags = [r.strip() for r in self.tags.get('TBR', '').split(',') if r.strip()]
    # TODO(crbug.com/839208): Remove support for 'Tbr:' when TBRs are
    # programmatically determined by self-CR+1s.
    footers = self.GitFootersFromDescription().get('Tbr', [])
    return sorted(set(tags + footers))

  # TODO(crbug.com/753425): Delete these once we're sure they're unused.
  @property
  def BUG(self):
    return ','.join(self.BugsFromDescription())

  @property
  def R(self):
    return ','.join(self.ReviewersFromDescription())

  @property
  def TBR(self):
    return ','.join(self.TBRsFromDescription())

  def AllFiles(self, root=None):
    """List all files under source control in the repo."""
    raise NotImplementedError()

  def AffectedFiles(self, include_deletes=True, file_filter=None):
    """Returns a list of AffectedFile instances for all files in the change.

    Args:
      include_deletes: If false, deleted files will be filtered out.
      file_filter: An additional filter to apply.

    Returns:
      [AffectedFile(path, action), AffectedFile(path, action)]
    """
    affected = list(filter(file_filter, self._affected_files))

    if include_deletes:
      return affected
    return list(filter(lambda x: x.Action() != 'D', affected))

  def AffectedTestableFiles(self, include_deletes=None, **kwargs):
    """Return a list of the existing text files in a change."""
    if include_deletes is not None:
      warn('AffectedTeestableFiles(include_deletes=%s)'
           ' is deprecated and ignored' % str(include_deletes),
           category=DeprecationWarning,
           stacklevel=2)
    return list(
        filter(lambda x: x.IsTestableFile(),
               self.AffectedFiles(include_deletes=False, **kwargs)))

  def AffectedTextFiles(self, include_deletes=None):
    """An alias to AffectedTestableFiles for backwards compatibility."""
    return self.AffectedTestableFiles(include_deletes=include_deletes)

  def LocalPaths(self):
    """Convenience function."""
    return [af.LocalPath() for af in self.AffectedFiles()]

  def AbsoluteLocalPaths(self):
    """Convenience function."""
    return [af.AbsoluteLocalPath() for af in self.AffectedFiles()]

  def RightHandSideLines(self):
    """An iterator over all text lines in 'new' version of changed files.

    Lists lines from new or modified text files in the change.

    This is useful for doing line-by-line regex checks, like checking for
    trailing whitespace.

    Yields:
      a 3 tuple:
        the AffectedFile instance of the current file;
        integer line number (1-based); and
        the contents of the line as a string.
    """
    return RightHandSideLinesImpl(
        x for x in self.AffectedFiles(include_deletes=False)
        if x.IsTestableFile())

  def OriginalOwnersFiles(self):
    """A map from path names of affected OWNERS files to their old content."""
    def owners_file_filter(f):
      return 'OWNERS' in os.path.split(f.LocalPath())[1]

    files = self.AffectedFiles(file_filter=owners_file_filter)
    return {f.LocalPath(): f.OldContents() for f in files}


class GitChange(Change):
  _AFFECTED_FILES = GitAffectedFile
  scm = 'git'

  def AllFiles(self, root=None):
    """List all files under source control in the repo."""
    root = root or self.RepositoryRoot()
    return subprocess.check_output(
        ['git', '-c', 'core.quotePath=false', 'ls-files', '--', '.'],
        cwd=root).decode('utf-8', 'ignore').splitlines()
