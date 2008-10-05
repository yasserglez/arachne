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
import pickle
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.indexer.task import CrawlTask


class TestCrawlTask(unittest.TestCase):

    def setUp(self):
        self._site_id = 'aa958756e769188be9f76fbdb291fe1b2ddd4777'
        self._url = 'ftp://deltha.uh.cu/'
        self._task = CrawlTask(self._site_id, self._url)

    def test_properties(self):
        revisit_wait = 60
        self.assertEquals(self._task.site_id, self._site_id)
        self.assertEquals(self._task.url, self._url)
        self.assertEquals(self._task.revisit_wait, 0)
        self.assertEquals(self._task.revisit_count, 0)
        self.assertEquals(self._task.change_count, 0)
        self._task.revisit_wait = revisit_wait
        self.assertEquals(self._task.revisit_wait, revisit_wait)

    def test_pickling(self):
        task = pickle.loads(pickle.dumps(self._task))
        self.assertEquals(self._task.site_id, task.site_id)
        self.assertEquals(self._task.url, task.url)
        self.assertEquals(self._task.revisit_wait, task.revisit_wait)
        self.assertEquals(self._task.revisit_count, task.revisit_count)
        self.assertEquals(self._task.change_count, task.change_count)

    def test_report_revisit(self):
        # Reporting a visit without changes.
        self._task.report_revisit(False)
        self.assertEquals(self._task.revisit_count, 1)
        self.assertEquals(self._task.change_count, 0)
        # Reporting a visit with changes.
        self._task.report_revisit(True)
        self.assertEquals(self._task.revisit_count, 2)
        self.assertEquals(self._task.change_count, 1)


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
