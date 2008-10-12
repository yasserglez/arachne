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

from arachne.task import CrawlTask


class TestCrawlTask(unittest.TestCase):

    def setUp(self):
        self._url = 'ftp://deltha.uh.cu/'
        self._site_id = 'aa958756e769188be9f76fbdb291fe1b2ddd4777'
        self._task = CrawlTask(self._site_id, self._url)

    def test_properties(self):
        self.assertEquals(self._task.site_id, self._site_id)
        self.assertEquals(self._task.url, self._url)
        self.assertEquals(self._task.revisit_wait, 0)
        self.assertEquals(self._task.revisit_count, 0)
        self.assertEquals(self._task.change_count, 0)

    def test_pickling(self):
        task = pickle.loads(pickle.dumps(self._task))
        self.assertEquals(self._task.site_id, task.site_id)
        self.assertEquals(self._task.url, task.url)
        self.assertEquals(self._task.revisit_wait, task.revisit_wait)
        self.assertEquals(self._task.revisit_count, task.revisit_count)
        self.assertEquals(self._task.change_count, task.change_count)

    def test_revisit_wait(self):
        # It should also reset counters for revisits and changes.
        revisit_wait = 60
        self._task.report_revisit(True)
        self._task.report_revisit(False)
        self._task.revisit_wait = revisit_wait
        self.assertEquals(self._task.revisit_wait, revisit_wait)
        self.assertEquals(self._task.revisit_count, 0)
        self.assertEquals(self._task.change_count, 0)

    def test_report_revisit(self):
        # Reporting visits without changes.
        visits = 10
        for i in xrange(visits):
            self._task.report_revisit(False)
            self.assertEquals(self._task.revisit_count, i + 1)
            self.assertEquals(self._task.change_count, 0)
        # Reporting visits with changes.
        for i in xrange(visits):
            self._task.report_revisit(True)
            self.assertEquals(self._task.revisit_count, visits + i + 1)
            self.assertEquals(self._task.change_count, i + 1)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', dest='verbosity', default='2',
                      type='choice', choices=['0', '1', '2'],
                      help='verbosity level: 0 = minimal, 1 = normal, 2 = all')
    options = parser.parse_args()[0]
    module = os.path.basename(__file__)[:-3]
    suite = unittest.TestLoader().loadTestsFromName(module)
    runner = unittest.TextTestRunner(verbosity=int(options.verbosity))
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
