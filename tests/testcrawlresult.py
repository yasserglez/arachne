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

from aracne.index.task import CrawlTask
from aracne.index.result import CrawlResult


class TestCrawlResult(unittest.TestCase):

    def setUp(self):
        self._found = True
        self._task = CrawlTask('aa958756e769188be9f76fbdb291fe1b2ddd4777',
                               'ftp://deltha.uh.cu/')
        self._result = CrawlResult(self._task, self._found)
        self._entries = (('a', {'isdir': True}), ('b', {'size': 1024}),
                         ('c', {'size': 2049}), ('d', {'isdir': True}))

    def test_properties(self):
        self.assertEquals(self._result.task.site_id, self._task.site_id)
        self.assertEquals(self._result.task.url, self._task.url)
        self.assertEquals(self._result.found, self._found)

    def test_entries(self):
        for entry, data in self._entries:
            self._result.append(entry, data)
        entries = [(self._task.url.join(entry), data)
                   for entry, data in self._entries]
        self.assertEquals(list(self._result), entries)

    def test_pickling(self):
        for entry, data in self._entries:
            self._result.append(entry, data)
        result = pickle.loads(pickle.dumps(self._result))
        self.assertEquals(self._result.task.site_id, result.task.site_id)
        self.assertEquals(self._result.task.url, result.task.url)
        self.assertEquals(self._result.found, result.found)
        self.assertEquals(list(self._result), list(result))


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
