#!/usr/bin/env vpython3
# coding=utf-8
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Unit tests for git_cl.py."""

import logging
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import git_auth
import scm
import scm_mock


class TestConfigChanger(unittest.TestCase):

    def setUp(self):
        scm_mock.GIT(self)

    def test_apply_new_auth(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {
                'credential.https://chromium.googlesource.com/.helper':
                ['', 'luci'],
                'http.cookiefile': [''],
            },
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_new_auth_sso(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH_SSO,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {
                'protocol.sso.allow': ['always'],
                'url.sso://chromium/.insteadof':
                ['https://chromium.googlesource.com/'],
                'http.cookiefile': [''],
            },
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_no_auth(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NO_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {},
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_chain_sso_new(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH_SSO,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {
                'credential.https://chromium.googlesource.com/.helper':
                ['', 'luci'],
                'http.cookiefile': [''],
            },
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_chain_new_sso(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH_SSO,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {
                'protocol.sso.allow': ['always'],
                'url.sso://chromium/.insteadof':
                ['https://chromium.googlesource.com/'],
                'http.cookiefile': [''],
            },
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_chain_new_no(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NO_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {},
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)

    def test_apply_chain_sso_no(self):
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NEW_AUTH_SSO,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        git_auth.ConfigChanger(
            mode=git_auth.ConfigMode.NO_AUTH,
            remote_url=
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git',
        ).apply('/some/fake/dir')
        want = {
            '/some/fake/dir': {},
        }
        self.assertEqual(scm.GIT._dump_config_state(), want)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG if '-v' in sys.argv else logging.ERROR)
    unittest.main()
