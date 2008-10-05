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

"""`CrawlResult` and `ResultQueue`.
"""

import os
import threading

from aracne.indexer.error import EmptyQueue
from aracne.utils.persist import Queue, QueueError


class CrawlResult(object):
    """Crawl result.

    This class represents the content of a directory.  It's the result of
    executing a `CrawlTask`.
    """

    def __init__(self, task, found):
        """Initialize a crawl result without entries.
        """
        self._task = task
        self._found = found
        self._entries = []

    def __iter__(self):
        """Iterate over entries in the directory.
        """
        return iter(self._entries)

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'task': self._task,
            'found': self._found,
            'entries': self._entries,
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self._task = state['task']
        self._found = state['found']
        self._entries = state['entries']

    def append(self, entry, data):
        """Append a new entry.
        """
        entry_url = self._task.url.join(entry)
        self._entries.append((entry_url, data))

    def _get_task(self):
        """Get method for the `task` property.
        """
        return self._task

    def _get_found(self):
        """Get method for the `found` property.
        """
        return self._found

    task = property(_get_task)

    found = property(_get_found)


class ResultQueue(object):
    """Crawl result queue.

    This queue is used to collect the crawl results waiting to be processed.
    """

    def __init__(self, sites_info, dir_path):
        """Initialize the queue.
        """
        sites_filename = 'sites.db'
        self._sites = Queue(os.path.join(dir_path, sites_filename))
        # Get the list files in the directory to purge old queues (sites
        # removed from the configuration file).
        old_queues = os.listdir(dir_path)
        old_queues.remove(sites_filename)
        self._results = {}
        for site_id, info in sites_info.iteritems():
            filename = '%s.db' % site_id
            queue = Queue(os.path.join(dir_path, filename))
            self._results[site_id] = queue
            if filename in old_queues:
                old_queues.remove(filename)
        for filename in old_queues:
            os.unlink(os.path.join(dir_path, filename))
        self._mutex = threading.Lock()

    def __len__(self):
        """Return the number of crawl results in the queue.
        """
        self._mutex.acquire()
        try:
            return sum(len(queue) for queue in self._results.itervalues())
        finally:
            self._mutex.release()

    def put(self, result):
        """Enqueue a crawl result.
        """
        self._mutex.acquire()
        try:
            site_id = result.task.site_id
            self._sites.put(site_id)
            self._results[site_id].put(result)
        finally:
            self._mutex.release()

    def get(self):
        """Return the crawl result at the head of the queue.

        This method does not remove the result from the queue until it's
        reported as processed using `report_done()`.  If there are not results
        available an `EmptyQueue` exception is raised.
        """
        self._mutex.acquire()
        try:
            while True:
                try:
                    site_id = self._sites.head()
                except QueueError:
                    raise EmptyQueue()
                else:
                    try:
                        result = self._results[site_id].head()
                    except KeyError:
                        # The head of the sites queue is an old site.
                        self._sites.get()
                    except QueueError:
                        # The result queue can be empty if a site is removed
                        # from the configuration file and added again.
                        self._sites.get()
                    else:
                        return result
        finally:
            self._mutex.release()

    def report_done(self, result):
        """Report a result as processed.

        This method removes the result at the head of the queue.
        """
        self._mutex.acquire()
        try:
            site_id = self._sites.get()
            self._results[site_id].get()
        finally:
            self._mutex.release()

    def sync(self):
        """Synchronize the queue on disk.
        """
        self._mutex.acquire()
        try:
            self._sites.sync()
            for queue in self._results.itervalues():
                queue.sync()
        finally:
            self._mutex.release()

    def close(self):
        """Close the queue.
        """
        self._mutex.acquire()
        try:
            self._sites.close()
            for queue in self._results.itervalues():
                queue.close()
        finally:
            self._mutex.release()
