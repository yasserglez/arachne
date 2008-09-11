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
import logging
import urlparse
import threading

from aracne.errors import EmptyQueueError
from aracne.utils.persist import Queue, QueueError


class CrawlResult(object):
    """Crawl result.

    It represents and contains the result of listing the files and directories
    found inside of a given directory.  It is the result of executing a
    `CrawlTask`.
    """

    siteid = property(lambda self: self._siteid)

    url = property(lambda self: self._url)

    found = property(lambda self: self._found)

    def __init__(self, siteid, url, found=True):
        """Initialize a crawl result without entries.
        """
        self._siteid = siteid
        self._url = url
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
            'siteid': self._siteid,
            'url': self._url,
            'found': self._found,
            'entries': self._entries,
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self._siteid = state['siteid']
        self._url = state['url']
        self._found = state['found']
        self._entries = state['entries']

    def append(self, entry, metadata):
        """Append a new entry to the crawl result of the directory.
        """
        # TODO: Appending entries to a not found result?
        url = urlparse.urljoin(self._url, entry)
        self._entries.append((url, metadata))


class ResultQueue(object):
    """Crawl result queue.

    It collects the crawl results waiting to be processed.
    """

    def __init__(self, dirname, sites):
        """Initialize the queue.
        """
        self._mutex = threading.Lock()
        # Open or create the queues.
        sitedbname = 'sites.db'
        self._sitesdb = Queue(os.path.join(dirname, sitedbname))
        self._resultdb = {}
        for site in sites:
            queuename = '%s.db' % site['siteid']
            queue = Queue(os.path.join(dirname, queuename))
            self._resultdb[site['siteid']] = queue
        # Remove old queues.
        oldqueues = os.listdir(dirname)
        oldqueues.remove(sitedbname)
        for site in sites:
            queuename = '%s.db' % site['siteid']
            oldqueues.remove(queuename)
        for filename in oldqueues:
            os.unlink(os.path.join(dirname, filename))

    def __len__(self):
        """Return the number of crawl results in the queue.
        """
        return sum(len(resultdb) for resultdb in self._resultdb.itervalues())

    def put(self, result):
        """Enqueue a result.

        Put the crawl result received as argument in the queue.
        """
        self._mutex.acquire()
        self._put(result)
        self._mutex.release()

    def get(self):
        """Return the crawl result at the head of the queue.

        This does not remove the result from the head of the queue until it is
        reported as processed using `report_done()`.  If there is not an
        available result an `EmptyQueueError` exception is raised.
        """
        self._mutex.acquire()
        try:
            return self._get()
        finally:
            self._mutex.release()

    def report_done(self, result):
        """Report a result as processed.

        This removes the result at the head of the queue.
        """
        self._mutex.acquire()
        self._report_done(result)
        self._mutex.release()

    def sync(self):
        """Synchronize the databases on disk.
        """
        self._mutex.acquire()
        self._sitesdb.sync()
        for resultdb in self._resultdb.itervalues():
            resultdb.sync()
        self._mutex.release()

    def close(self):
        """Close the databases.
        """
        self._mutex.acquire()
        self._sitesdb.close()
        for resultdb in self._resultdb.itervalues():
            resultdb.close()
        self._mutex.release()

    def _put(self, result):
        """Enqueue a result.
        """
        self._sitesdb.put(result.siteid)
        self._resultdb[result.siteid].put(result)

    def _get(self):
        """Return the result at the top of the queue.
        """
        while True:
            try:
                siteid = self._sitesdb.head()
            except QueueError:
                raise EmptyQueueError()
            else:
                try:
                    result = self._resultdb[siteid].head()
                except KeyError:
                    # The head of the sites db is the id of an old site.
                    # Remove it and try to get another.
                    self._sitesdb.get()
                else:
                    return result

    def _report_done(self, result):
        """Report a result as processed.
        """
        siteid = self._sitesdb.get()
        self._resultdb[siteid].get()
