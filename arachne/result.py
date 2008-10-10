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

"""Queue for crawl results and the crawl result definition.
"""

import os
import sys
import glob
import bsddb
import pickle
import threading

from arachne.error import EmptyQueue


class CrawlResult(object):
    """Crawl result.

    This class represents the content of a directory.  It is the result of
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

    def __init__(self, sites_info, db_home):
        """Initialize the queue.
        """
        self._mutex = threading.Lock()
        # Initialize the Berkeley DB environment.  This environment will
        # contain Btree databases with duplicated records (unsorted).  Records
        # in all databases use the same key (self._db_key), so, they will be
        # organized by the order of insertion.
        self._db_env = bsddb.db.DBEnv()
        self._db_env.open(db_home, bsddb.db.DB_CREATE | bsddb.db.DB_RECOVER
                          | bsddb.db.DB_INIT_TXN | bsddb.db.DB_INIT_LOG
                          | bsddb.db.DB_INIT_MPOOL)
        self._db_key = '0'.zfill(len(str(sys.maxint)))
        # Create the database for the sites.
        sites_db_name = 'sites.db'
        self._sites_db = bsddb.db.DB(self._db_env)
        self._sites_db.set_flags(bsddb.db.DB_DUP)
        self._sites_db.open(sites_db_name, bsddb.db.DB_BTREE,
                            bsddb.db.DB_CREATE | bsddb.db.DB_AUTO_COMMIT)
        # Get the list of databases to purge old ones (sites that were removed
        # from the configuration file).
        old_dbs = [os.path.basename(db_path)
                   for db_path in glob.glob('%s/*.db' % db_home.rstrip('/'))]
        old_dbs.remove(sites_db_name)
        # Open or create databases for results.
        self._result_dbs = {}
        for site_id, info in sites_info.iteritems():
            result_db_name = '%s.db' % site_id
            result_db = bsddb.db.DB(self._db_env)
            result_db.set_flags(bsddb.db.DB_DUP)
            result_db.open(result_db_name, bsddb.db.DB_BTREE,
                           bsddb.db.DB_CREATE | bsddb.db.DB_AUTO_COMMIT)
            self._result_dbs[site_id] = result_db
            if result_db_name in old_dbs:
                old_dbs.remove(result_db_name)

    def __len__(self):
        """Return the number of crawl results in the queue.
        """
        self._mutex.acquire()
        try:
            return sum(len(result_db)
                       for result_db in self._result_dbs.itervalues())
        finally:
            self._mutex.release()

    def put(self, result):
        """Enqueue a crawl result.
        """
        self._mutex.acquire()
        try:
            site_id = result.task.site_id
            result_db = self._result_dbs[site_id]
            self._sites_db.put(self._db_key, site_id)
            result_db.put(self._db_key, pickle.dumps(result))
        finally:
            self._mutex.release()

    def get(self):
        """Return the crawl result at the head of the queue.

        This method does not remove the result from the queue until it is
        reported as processed using `report_done()`.  If there are not results
        available an `EmptyQueue` exception is raised.
        """
        self._mutex.acquire()
        try:
            result = None
            while result is None:
                if not self._sites_db:
                    raise EmptyQueue('Queue without results.')
                else:
                    transaction = self._db_env.txn_begin()
                    sites_cursor = self._sites_db.cursor(transaction)
                    site_id = sites_cursor.first()[1]
                    try:
                        result_db = self._result_dbs[site_id]
                    except KeyError:
                        # The head of the sites databse is an old site.
                        sites_cursor.delete()
                    else:
                        if not result_db:
                            # The database can be empty if a site is removed
                            # from the configuration file and added again.
                            sites_cursor.delete()
                        else:
                            result_cursor = result_db.cursor(transaction)
                            result = pickle.loads(result_cursor.first()[1])
                            result_cursor.close()
                    sites_cursor.close()
                    transaction.commit()
            return result
        finally:
            self._mutex.release()

    def report_done(self, result):
        """Report a result as processed.

        This method removes the result at the head of the queue.
        """
        self._mutex.acquire()
        try:
            site_id = result.task.site_id
            result_db = self._result_dbs[site_id]
            transaction = self._db_env.txn_begin()
            sites_cursor = self._sites_db.cursor(transaction)
            sites_cursor.first()
            sites_cursor.delete()
            sites_cursor.close()
            result_cursor = result_db.cursor(transaction)
            result_cursor.first()
            result_cursor.delete()
            result_cursor.close()
            transaction.commit()
        finally:
            self._mutex.release()

    def sync(self):
        """Synchronize the queue on disk.
        """
        self._mutex.acquire()
        try:
            self._sites_db.sync()
            for result_db in self._result_dbs.itervalues():
                result_db.sync()
        finally:
            self._mutex.release()

    def close(self):
        """Close the queue.
        """
        self._mutex.acquire()
        try:
            self._sites_db.close()
            for result_db in self._result_dbs.itervalues():
                result_db.close()
            self._db_env.close()
        finally:
            self._mutex.release()
