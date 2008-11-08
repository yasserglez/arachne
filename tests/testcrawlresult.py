# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
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

from arachne.result import CrawlResult
from arachne.task import CrawlTask
from arachne.url import URL


class TestCrawlResult(unittest.TestCase):

    def setUp(self):
        url = URL('ftp://deltha.uh.cu/')
        site_id = 'aa958756e769188be9f76fbdb291fe1b2ddd4777'
        self._num_entries = 10
        self._found = True
        self._task = CrawlTask(site_id, url)
        self._entries = [(str(i), {'is_dir': i < (self._num_entries / 2)})
                         for i in range(self._num_entries)]
        self._result = CrawlResult(self._task, self._found)

    def test_properties(self):
        self.assertEquals(self._result.task.site_id, self._task.site_id)
        self.assertEquals(str(self._result.task.url), str(self._task.url))
        self.assertEquals(self._result.found, self._found)

    def test_append_and_iter(self):
        for entry, data in self._entries:
            self._result.append(entry, data)
        entries = map(lambda i: i[0], self._entries)
        for entry, data in self._result:
            entries.remove(entry)
        self.assertEquals(len(entries), 0)

    def test_contains(self):
        entry, data = self._entries[0]
        self._result.append(entry, data)
        self.assertTrue(entry in self._result)
        self.assertFalse(entry * 2 in self._result)

    def test_len(self):
        for entry, data in self._entries:
            self._result.append(entry, data)
        self.assertEquals(len(self._result), self._num_entries)

    def test_getitem(self):
        entry, data = self._entries[0]
        self._result.append(entry, data)
        self.assertEquals(self._result[entry], data)
        self.assertRaises(KeyError, self._result.__getitem__, entry * 2)

    def test_pickling(self):
        for entry, data in self._entries:
            self._result.append(entry, data)
        result = pickle.loads(pickle.dumps(self._result))
        self.assertEquals(self._result.task.site_id, result.task.site_id)
        self.assertEquals(str(self._result.task.url), str(result.task.url))
        self.assertEquals(self._result.found, result.found)
        entries = map(lambda i: i[0], self._entries)
        for entry, data in result:
            entries.remove(entry)
        self.assertEquals(len(entries), 0)


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
