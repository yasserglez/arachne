#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Yasser González Fernández <yglez@uh.cu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import shutil
import hashlib
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.utils.url import URL
from aracne.errors import EmptyQueueError
from aracne.result import CrawlResult, ResultQueue


class TestResultQueue(unittest.TestCase):

    def setUp(self):
        self._dirname = os.path.join(TESTDIR, 'testresultqueue')
        os.mkdir(self._dirname)
        self._sites = [
            # Keep URLs different so they generate different site ids.
            {'url': URL('ftp://atlantis.uh.cu/')},
            {'url': URL('ftp://andromeda.uh.cu/')},
            {'url': URL('ftp://deltha.uh.cu/')},
        ]
        self._results = []
        for site in self._sites:
            site['siteid'] = hashlib.sha1(str(site['url'])).hexdigest()
            for name in 'abcdefghijklmnopqrstuvwxyz':
                result = CrawlResult(site['siteid'], site['url'].join(name))
                self._results.append(result)
        self._queue = ResultQueue(self._dirname, self._sites)

    def test_length(self):
        self.assertEquals(len(self._queue), 0)
        for i, result in enumerate(self._results):
            self._queue.put(result)
            self.assertEquals(len(self._queue), i + 1)
        for i in xrange(len(self._results)):
            result = self._queue.get()
            self._queue.report_done(result)
            self.assertEquals(len(self._queue), len(self._results) - i - 1)

    def test_populating(self):
        self.assertRaises(EmptyQueueError, self._queue.get)
        for result in self._results:
            self._queue.put(result)
        for result in self._results:
            returned_result = self._queue.get()
            self.assertEquals(returned_result.siteid, result.siteid)
            self._queue.report_done(returned_result)
        self.assertRaises(EmptyQueueError, self._queue.get)

    def test_closing(self):
        for result in self._results:
            self._queue.put(result)
        self._queue.close()
        # Close the queue, remove one site from the list and then open the
        # queue again.  It should not return crawl results from the removed
        # site but it should keep the order of the other results.
        del self._sites[0]
        self._queue = ResultQueue(self._dirname, self._sites)
        for result in self._results:
            if result.siteid in [site['siteid'] for site in self._sites]:
                returned_result = self._queue.get()
                self.assertEquals(returned_result.siteid, result.siteid)
                self._queue.report_done(returned_result)

    def tearDown(self):
        if os.path.isdir(self._dirname):
            self._queue.close()
            shutil.rmtree(self._dirname)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', dest='verbosity', default='2',
                      type='choice', choices=['0', '1', '2'],
                      help='verbosity level: 0 = minimal, 1 = normal, 2 = all')
    options, args = parser.parse_args()
    module = os.path.basename(__file__)[:-3]
    suite = unittest.TestLoader().loadTestsFromName(module)
    runner = unittest.TextTestRunner(verbosity=int(options.verbosity))
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
