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
import random
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.utils.persist import PriorityQueue, QueueError


class TestPriorityQueue(unittest.TestCase):

    def setUp(self):
        self._filename = os.path.join(TESTDIR, 'testpriorityqueue.db')
        self._items = [(i, i) for i in range(100)]
        self._queue = PriorityQueue(self._filename)

    def test_isempty(self):
        self.assertTrue(self._queue.isempty())
        self._queue.put(self._items[0][0], self._items[0][1])
        self.assertFalse(self._queue.isempty())
        self._queue.get()
        self.assertTrue(self._queue.isempty())

    def test_head(self):
        self.assertRaises(QueueError, self._queue.head)
        self._queue.put(self._items[0][0], self._items[0][1])
        self.assertEquals(self._queue.head(), self._items[0])
        self._queue.put(self._items[1][0], self._items[1][1])
        self.assertEquals(self._queue.head(), self._items[0])

    def test_tail(self):
        self.assertRaises(QueueError, self._queue.head)
        self._queue.put(self._items[0][0], self._items[0][1])
        self.assertEquals(self._queue.tail(), self._items[0])
        self._queue.put(self._items[1][0], self._items[1][1])
        self.assertEquals(self._queue.tail(), self._items[1])

    def test_length(self):
        self.assertEquals(len(self._queue), 0)
        for i, item in enumerate(self._items):
            self._queue.put(item[0], item[1])
            self.assertEquals(len(self._queue), i + 1)
        for i in xrange(len(self._items)):
            self._queue.get()
            self.assertEquals(len(self._queue), len(self._items) - i - 1)

    def test_populate(self):
        self.assertRaises(QueueError, self._queue.get)
        random_items = random.sample(self._items, len(self._items))
        for item in random_items:
            self._queue.put(item[0], item[1])
        random_items.sort(key=lambda item: item[1])
        for item in random_items:
            self.assertEquals(self._queue.get(), item)
        self.assertRaises(QueueError, self._queue.get)

    def test_persist(self):
        for item in self._items:
            self._queue.put(item[0], item[1])
        self._queue.close()
        self._queue = PriorityQueue(self._filename)
        for item in self._items:
            self.assertEquals(self._queue.get(), item)

    def tearDown(self):
        if os.path.isfile(self._filename):
            self._queue.close()
            os.unlink(self._filename)


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
