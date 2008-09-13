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

from aracne.task import CrawlTask


class TestCrawlTask(unittest.TestCase):

    def setUp(self):
        self._siteid = 'aa958756e769188be9f76fbdb291fe1b2ddd4777'
        self._url = 'ftp://deltha.uh.cu/'
        self._updatefactor_default = 1
        self._updatefactor_modify = 2
        self._task = CrawlTask(self._siteid, self._url)

    def test_properties(self):
        self.assertEquals(self._task.siteid, self._siteid)
        self.assertEquals(self._task.url, self._url)
        self.assertEquals(self._task.updatefactor, self._updatefactor_default)
        self._task.updatefactor = self._updatefactor_modify
        self.assertEquals(self._task.updatefactor, self._updatefactor_modify)

    def test_pickling(self):
        loaded_task = pickle.loads(pickle.dumps(self._task))
        self.assertEquals(self._task.siteid, loaded_task.siteid)
        self.assertEquals(self._task.url, loaded_task.url)
        self.assertEquals(self._task.updatefactor, loaded_task.updatefactor)


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
