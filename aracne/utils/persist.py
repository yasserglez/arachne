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

"""Persistent data structures.
"""

import os
import sys
import bsddb
import cPickle


class QueueError(Exception):
    """Base class for all queue exceptions.
    """


class PriorityQueue(object):
    """Persistent priority queue.
    """

    def __init__(self, filename):
        """Initialize the priority queue.
        """
        self._db = bsddb.db.DB()
        self._db.set_bt_compare(self._compare_keys)
        self._db.open(filename, bsddb.db.DB_BTREE, bsddb.db.DB_CREATE)

    def __len__(self):
        """Return the number of items in the queue.
        """
        return len(self._db)

    def put(self, item, priority):
        """Append a new item to the queue.

        Append a new item to the queue.  The item can be any pickable Python
        object and the priority should be a positive integer (or long integer).
        """
        self._put(item, priority)

    def head(self):
        """Return the item at the head of the queue.

        Return a (item, priority) tuple for the item at the head of the queue.
        This item will be a copy of the item saved in the database and if you
        modify it the changes will not be reflected in the database.
        """
        return self._head()

    def tail(self):
        """Return the item at the tail of the queue.

        Return a (item, priority) tuple for the item at the tail of the queue.
        This item will be a copy of the item saved in the database and if you
        modify it the changes will not be reflected in the database.
        """
        return self._tail()

    def isempty(self):
        """Return a boolean value indicating if the queue is empty.
        """
        return len(self._db) == 0

    def get(self):
        """Return the item at the head of the queue.

        Return and delete the item at the head of the queue.  If the queue is
        empty a `QueueError` exception is raised.
        """
        return self._get()

    def sync(self):
        """Synchronize the database on disk.
        """
        self._db.sync()

    def close(self):
        """Close the database.
        """
        self._db.close()

    def _compare_keys(self, key1, key2):
        """Method used to compare the keys of the BTree.
        """
        len1, len2 = len(key1), len(key2)
        if len1 > len2:
            return 1
        elif len1 < len2:
            return -1
        else:
            for c1, c2 in zip(key1, key2):
                n = cmp(c1, c2)
                if n != 0:
                    return n
            return 0

    def _put(self, item, priority):
        """Append a new item to the queue with the specified priority.
        """
        self._db.put(str(priority), cPickle.dumps(item, 2))

    def _head(self):
        """Return the item at the head of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            cursor = self._db.cursor()
            priority, item = cursor.first()
            cursor.close()
            return (cPickle.loads(item), long(priority))

    def _tail(self):
        """Return the item at the tail of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            cursor = self._db.cursor()
            priority, item = cursor.last()
            cursor.close()
            return (cPickle.loads(item), long(priority))

    def _get(self):
        """Return and delete the item at the head of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            cursor = self._db.cursor()
            priority, item = cursor.first()
            cursor.delete()
            cursor.close()
            return (cPickle.loads(item), long(priority))


class Queue(PriorityQueue):
    """Persistent queue.
    """

    def __init__(self, filename):
        """Initialize the queue.
        """
        self._priority = 0
        self._db = bsddb.db.DB()
        self._db.set_flags(bsddb.db.DB_DUP)
        self._db.open(filename, bsddb.db.DB_BTREE, bsddb.db.DB_CREATE)
        self._db.sync()

    def put(self, item):
        """Append a new item to the queue.

        Append a new item to tail the queue.  The item can be any pickable
        Python object.
        """
        PriorityQueue._put(self, item, self._priority)

    def head(self):
        """Return the item at the head of the queue.

        This returned item will be a copy of the item saved in the database and
        you should not modify it.
        """
        item, priority = PriorityQueue._head(self)
        return item

    def tail(self):
        """Return the item at the tail of the queue.

        The returned item will be a copy of the item saved in the database and
        you should not modify it.
        """
        item, priority = PriorityQueue._tail(self)
        return item

    def get(self):
        """Return the item at the head of the queue.

        Return and delete the item at the head of the queue.  If the queue is
        empty a `QueueError` exception is raised.
        """
        item, priority = PriorityQueue._get(self)
        return item
