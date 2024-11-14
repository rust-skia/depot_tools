# Copyright 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from recipe_engine import post_process

PYTHON_VERSION_COMPATIBILITY = 'PY3'

DEPS = [
    'bot_update',
    'gclient',
    'recipe_engine/buildbucket',
    'recipe_engine/json',
    'recipe_engine/properties',
]


def RunSteps(api):
  config = api.gclient.make_config()
  config.got_revision_reverse_mapping['got_revision'] = 'src'
  sln = config.solutions.add()
  sln.name = 'src'
  sln.url = api.properties.get('git_repo')
  api.gclient.c = config
  api.bot_update.ensure_checkout(set_output_commit=True,
                                 parse_commit_position=api.properties.get(
                                     'parse_commit_position', True))


def GenTests(api):

  def json_output(repository, revision, got_revision_cp=None):
    output = {
        'did_run': True,
        "manifest": {
            "src": {
                "repository": repository,
                "revision": revision
            }
        },
        "patch_root": None,
        "properties": {
            "got_revision": revision,
        },
        "root": "src",
        "step_text": "text"
    }
    if got_revision_cp:
      output['properties']['got_revision_cp'] = got_revision_cp
    return output

  yield api.test(
      'got_revision_cp',
      api.properties(git_repo='https://fake.org/repo.git'),
      api.buildbucket.ci_build(git_repo='https://fake.org/repo.git',
                               git_ref='refs/tags/100.0.0000.0',
                               revision='1234567890'),
      api.step_data(
          'bot_update',
          api.json.output(
              json_output(repository='https://fake.org/repo.git',
                          revision='1234567890',
                          got_revision_cp='refs/branch-heads/1000@{#1}'))),
      api.post_process(
          post_process.PropertyEquals,
          '$recipe_engine/buildbucket/output_gitiles_commit',
          {
              'host': 'fake.org',
              'id': '1234567890',
              'position': 1,
              'project': 'repo',
              'ref': 'refs/branch-heads/1000'
          },
      ),
      api.post_process(post_process.DropExpectation),
  )

  yield api.test(
      'got_revision_cp_do_not_parse_commit_position',
      api.properties(
          git_repo='https://chromium.googlesource.com/chromium/src.git',
          parse_commit_position=False),
      api.buildbucket.ci_build(
          git_repo='https://chromium.googlesource.com/chromium/src.git',
          git_ref='refs/tags/100.0.0000.0',
          revision='1234567890'),
      api.step_data(
          'bot_update',
          api.json.output(
              json_output(repository=
                          "https://chromium.googlesource.com/chromium/src.git",
                          revision='1234567890',
                          got_revision_cp='got_revision_cp'))),
      api.post_process(
          post_process.PropertyEquals,
          '$recipe_engine/buildbucket/output_gitiles_commit',
          {
              'host': 'chromium.googlesource.com',
              'id': '1234567890',
              'project': 'chromium/src',
              'ref': 'refs/tags/100.0.0000.0'
          },
      ),
      api.post_process(post_process.DropExpectation),
  )

  yield api.test(
      'no_got_revision_cp_ref_revision',
      api.properties(git_repo='https://fake.org/repo.git'),
      api.buildbucket.ci_build(git_repo='https://fake.org/repo.git',
                               git_ref='refs/branch-heads/1000',
                               revision='refs/refname'),
      api.step_data(
          'bot_update',
          api.json.output(
              json_output(repository='https://fake.org/repo.git',
                          revision='1234567890'))),
      api.post_process(
          post_process.PropertyEquals,
          '$recipe_engine/buildbucket/output_gitiles_commit',
          {
              'host': 'fake.org',
              'id': '1234567890',
              'project': 'repo',
              'ref': 'refs/refname'
          },
      ),
      api.post_process(post_process.DropExpectation),
  )

  yield api.test(
      'no_got_revision_cp_head_revision',
      api.properties(git_repo='https://fake.org/repo.git'),
      api.buildbucket.ci_build(git_repo='https://fake.org/repo.git',
                               git_ref='refs/branch-heads/1000',
                               revision='HEAD'),
      api.step_data(
          'bot_update',
          api.json.output(
              json_output(repository='https://fake.org/repo.git',
                          revision='1234567890'))),
      api.post_process(
          post_process.PropertyEquals,
          '$recipe_engine/buildbucket/output_gitiles_commit',
          {
              'host': 'fake.org',
              'id': '1234567890',
              'project': 'repo',
              'ref': 'refs/heads/main'
          },
      ),
      api.post_process(post_process.DropExpectation),
  )

  yield api.test(
      'out_commit_id_equals_in_commit_id',
      api.properties(git_repo='https://fake.org/repo.git'),
      api.buildbucket.ci_build(git_repo='https://fake.org/repo.git',
                               git_ref='refs/branch-heads/1000',
                               revision='1234567890'),
      api.step_data(
          'bot_update',
          api.json.output(
              json_output(repository='https://fake.org/repo.git',
                          revision='1234567890'))),
      api.post_process(
          post_process.PropertyEquals,
          '$recipe_engine/buildbucket/output_gitiles_commit',
          {
              'host': 'fake.org',
              'id': '1234567890',
              'project': 'repo',
              'ref': 'refs/branch-heads/1000'
          },
      ),
      api.post_process(post_process.DropExpectation),
  )
