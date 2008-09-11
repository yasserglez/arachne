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
import urlparse
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.result import CrawlResult


class TestCrawlResult(unittest.TestCase):

    def setUp(self):
        self._siteid = 'aa958756e769188be9f76fbdb291fe1b2ddd4777'
        self._url = 'ftp://deltha.uh.cu/'
        self._found = True
        self._entries = (('directory', {}), ('file', {'size': 1024}))
        self._result = CrawlResult(self._siteid, self._url, self._found)

    def test_properties(self):
        self.assertEquals(self._result.siteid, self._siteid)
        self.assertEquals(self._result.url, self._url)
        self.assertEquals(self._result.found, self._found)

    def test_entries(self):
        for entry, metadata in self._entries:
            self._result.append(entry, metadata)
        self._entries = [(urlparse.urljoin(self._url, entry), metadata)
                         for entry, metadata in self._entries]
        self.assertEquals(list(self._result), self._entries)

    def test_pickling(self):
        for entry, metadata in self._entries:
            self._result.append(entry, metadata)
        loaded_result = pickle.loads(pickle.dumps(self._result))
        self.assertEquals(self._result.siteid, loaded_result.siteid)
        self.assertEquals(self._result.url, loaded_result.url)
        self.assertEquals(self._result.found, loaded_result.found)
        self.assertEquals(list(self._result), list(loaded_result))


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
