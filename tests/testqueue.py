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
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.utils.persist import Queue, QueueError


class TestQueue(unittest.TestCase):

    def setUp(self):
        self._filename = os.path.join(TESTDIR, 'testqueue.db')
        self._numitems = 100
        self._queue = Queue(self._filename)

    def test_isempty(self):
        self.assertTrue(self._queue.isempty())
        self._queue.put(0)
        self.assertFalse(self._queue.isempty())
        self._queue.get()
        self.assertTrue(self._queue.isempty())

    def test_head(self):
        self.assertRaises(QueueError, self._queue.head)
        self._queue.put(0)
        self.assertEquals(self._queue.head(), 0)
        self._queue.put(1)
        self.assertEquals(self._queue.head(), 0)

    def test_tail(self):
        self.assertRaises(QueueError, self._queue.head)
        self._queue.put(0)
        self.assertEquals(self._queue.tail(), 0)
        self._queue.put(1)
        self.assertEquals(self._queue.tail(), 1)

    def test_length(self):
        self.assertEquals(len(self._queue), 0)
        for i in xrange(1, self._numitems + 1):
            self._queue.put(i)
            self.assertEquals(len(self._queue), i)
        for i in xrange(1, self._numitems + 1):
            self._queue.get()
            self.assertEquals(len(self._queue), self._numitems - i)

    def test_put(self):
        for i in xrange(self._numitems):
            self._queue.put(i)
        for i in xrange(self._numitems):
            self.assertEquals(self._queue.get(), i)

    def test_get(self):
        # Here I just test if the exception is raised if empty.  Getting item
        # from the queue is already tested in test_put().
        self.assertRaises(QueueError, self._queue.get)

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
