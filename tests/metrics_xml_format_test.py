#!/usr/bin/env vpython3
# coding=utf-8
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gclient_paths_test
import metrics_xml_format

norm = lambda path: path.replace('/', os.sep)
join = os.path.join


class TestBase(gclient_paths_test.TestBase):

    def setUp(self):
        super().setUp()

        # os.path.abspath() doesn't seem to use os.path.getcwd() to compute
        # the abspath of a given path.
        #
        # This mock os.path.abspath such that it uses the mocked getcwd().
        mock.patch('os.path.abspath', self.abspath).start()
        # gclient_paths.GetPrimarysolutionPath() defaults to src.
        self.make_file_tree({'.gclient': ''})
        self.cwd = join(self.cwd, 'src')

    def abspath(self, path):
        if os.path.isabs(path):
            return path

        return join(self.getcwd(), path)


class GetMetricsDirTest(TestBase):

    def testWithAbsolutePath(self):
        get = lambda path: metrics_xml_format.GetMetricsDir(norm(path))
        self.assertTrue(get('/src/tools/metrics/actions/abc.xml'))
        self.assertTrue(get('/src/tools/metrics/histograms/abc.xml'))
        self.assertTrue(get('/src/tools/metrics/structured/abc.xml'))
        self.assertTrue(get('/src/tools/metrics/ukm/abc.xml'))

        self.assertFalse(get('/src/tools/metrics/actions/next/abc.xml'))
        self.assertFalse(get('/src/tools/metrics/histograms/next/abc.xml'))
        self.assertFalse(get('/src/tools/metrics/structured/next/abc.xml'))
        self.assertFalse(get('/src/tools/metrics/ukm/next/abc.xml'))

    def testWithRelativePaths(self):
        get = lambda path: metrics_xml_format.GetMetricsDir(norm(path))
        self.cwd = join(self.cwd, 'tools')
        self.assertFalse(get('abc.xml'))
        self.assertTrue(get('metrics/actions/abc.xml'))


class FindMetricsXMLFormatTool(TestBase):

    def testWithMetricsXML(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool

        self.assertEqual(
            findTool(norm('tools/metrics/actions/abc.xml')),
            join(self.getcwd(), norm('tools/metrics/actions/pretty_print.py')),
        )

        # same test, but with an absolute path.
        self.assertEqual(
            findTool(join(self.getcwd(),
                          norm('tools/metrics/actions/abc.xml'))),
            join(self.getcwd(), norm('tools/metrics/actions/pretty_print.py')),
        )

    def testWthNonMetricsXML(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool
        self.assertEqual(findTool('tools/metrics/actions/next/abc.xml'), '')

    def testWithNonCheckout(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool
        self.cwd = self.root
        self.assertEqual(findTool('tools/metrics/actions/abc.xml'), '')

    def testWithDifferentCheckout(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool
        checkout2 = join(self.root, '..', self._testMethodName + '2', 'src')
        self.assertEqual(
            # this is the case the tool was given a file path that is located
            # in a different checkout folder.
            findTool(join(checkout2, norm('tools/metrics/actions/abc.xml'))),
            '',
        )

    def testSupportedHistogramsXML(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool
        self.assertEqual(
            findTool(norm('tools/metrics/histograms/enums.xml')),
            join(self.getcwd(),
                 norm('tools/metrics/histograms/pretty_print.py')),
        )

    def testNotSupportedHistogramsXML(self):
        findTool = metrics_xml_format.FindMetricsXMLFormatterTool
        self.assertEqual(findTool(norm('tools/metrics/histograms/NO.xml')), '')


if __name__ == '__main__':
    unittest.main()
