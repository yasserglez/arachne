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
import cPickle as pickle


class QueueError(Exception):
    """Base class for exceptions related with the queues.
    """


class PriorityQueue(object):
    """Persistent priority queue.
    """

    def __init__(self, filename):
        """Initialize the priority queue.
        """
        isnewdb = not os.path.isfile(filename)
        self._keyencoding = 'utf-8'
        self._counterkey = 'counter'
        self._keylength = len(str(sys.maxint))
        self._db = bsddb.btopen(filename)
        if isnewdb:
            self._counter = 0
            self._save(self._counter, self._counterkey)
        else:
            self._counter = self._load(self._counterkey)
        self._db.sync()

    def __len__(self):
        """Return the number of items in the queue.
        """
        return self._counter

    def put(self, item, priority):
        """Append a new item to the queue.

        Append a new item to the queue.  The item can be any pickable Python
        object and the priority should be a positive integer.
        """
        self._put(item, priority)

    def head(self):
        """Return the item at the head of the queue.

        Return a (item, priority) tuple for the item at the head of the queue.
        This item will be a copy of the item saved in the database and you
        should not modify it.
        """
        return self._head()

    def tail(self):
        """Return the item at the tail of the queue.

        Return a (item, priority) tuple for the item at the tail of the queue.
        This item will be a copy of the item saved in the database and you
        should not modify it.
        """
        return self._tail()

    def isempty(self):
        """Return a boolean value indicating if the queue is empty.
        """
        return (self._counter == 0)

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

    def _save(self, obj, key):
        """Save the object in the database.
        """
        self._db[key.encode(self._keyencoding)] = pickle.dumps(obj, 2)

    def _load(self, key):
        """Load and return the object associated with the key.
        """
        return pickle.loads(self._db[key.encode(self._keyencoding)])

    def _increase_counter(self):
        """Increase items counter.

        Increase by one the counter for the number of items in the queue and
        update the value saved in the database.
        """
        self._counter += 1
        self._save(self._counter, self._counterkey)

    def _decrease_counter(self):
        """Decrease the items counter.

        Decrease by one the counter for the number of items in the queue and
        updated the value saved in the database.
        """
        self._counter -= 1
        self._save(self._counter, self._counterkey)

    def _put(self, item, priority):
        """Append a new item to the queue with the specified priority.
        """
        self._save(item, str(priority).zfill(self._keylength))
        self._increase_counter()

    def _head(self):
        """Return the item at the head of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            key = self._db.first()[0]
            item = self._load(key)
            return (item, int(key))

    def _tail(self):
        """Return the item at the tail of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            # The last key in the BTree is the counter.
            self._db.last()
            key = self._db.previous()[0]
            item = self._load(key)
            return (item, int(key))

    def _get(self):
        """Return and delete the item at the head of the queue.
        """
        if self.isempty():
            raise QueueError()
        else:
            key = self._db.first()[0]
            # TODO: If I leave the cursor there I get a DBNotFoundError
            # exception when _get() is invoked again.
            self._db.last()
            item = self._load(key)
            del self._db[key]
            self._decrease_counter()
            return (item, int(key))


class Queue(PriorityQueue):
    """Persistent queue.
    """

    def __init__(self, filename):
        """Initialize the queue.
        """
        PriorityQueue.__init__(self, filename)

    def put(self, item):
        """Append a new item to the queue.

        Append a new item to tail the queue.  The item can be any pickable
        Python object.
        """
        PriorityQueue._put(self, item, self._counter)

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
