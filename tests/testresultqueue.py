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
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.utils.url import URL
from aracne.task import CrawlTask
from aracne.errors import EmptyQueueError
from aracne.result import CrawlResult, ResultQueue


class TestResultQueue(unittest.TestCase):

    def setUp(self):
        self._dirname = os.path.join(TESTDIR, 'testresultqueue')
        os.mkdir(self._dirname)
        self._sites_info = {
            'a78e6853355ad5cdc751ad678d15339382f9ed21':
                {'url': URL('ftp://atlantis.uh.cu/')},
            '7e019d6f671d336a0cc31f137ba034efb13fc327':
                {'url': URL('ftp://andromeda.uh.cu/')},
            'aa958756e769188be9f76fbdb291fe1b2ddd4777':
                {'url': URL('ftp://deltha.uh.cu/')},
        }
        self._results = []
        for site_id, info in self._sites_info.iteritems():
            for name in (str(n) for n in xrange(10)):
                task = CrawlTask(site_id, info['url'].join(name))
                self._results.append(CrawlResult(task))
        self._queue = ResultQueue(self._dirname, self._sites_info)

    def test_length(self):
        self.assertEquals(len(self._queue), 0)
        for i, result in enumerate(self._results):
            self._queue.put(result)
            self.assertEquals(len(self._queue), i + 1)
        num_results = len(self._results)
        for i in xrange(len(self._results)):
            result = self._queue.get()
            self._queue.report_done(result)
            self.assertEquals(len(self._queue), num_results - i - 1)

    def test_populate(self):
        self.assertRaises(EmptyQueueError, self._queue.get)
        for result in self._results:
            self._queue.put(result)
        for result in self._results:
            returned = self._queue.get()
            self.assertEquals(returned.task.site_id, result.task.site_id)
            self.assertEquals(str(returned.task.url), str(result.task.url))
            self._queue.report_done(result)
        self.assertRaises(EmptyQueueError, self._queue.get)

    def test_persist(self):
        for result in self._results:
            self._queue.put(result)
        self._queue.close()
        # Remove a site from the list and open the queue again.  It should not
        # return results from this site but keep the order of the others.
        del self._sites_info[self._sites_info.keys()[0]]
        self._queue = ResultQueue(self._dirname, self._sites_info)
        for result in self._results:
            if self._sites_info.has_key(result.task.site_id):
                returned = self._queue.get()
                self.assertEquals(returned.task.site_id, result.task.site_id)
                self.assertEquals(str(returned.task.url), str(result.task.url))
                self._queue.report_done(returned)

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
