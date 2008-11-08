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

"""Crawl task and task queue.
"""


import os
import sys
import time
import glob
import math
import bsddb
import cPickle
import logging
import threading

from arachne.error import EmptyQueue


class CrawlTask(object):
    """Crawl task.

    This class represents an action to list the content of a directory.
    Executing a task produces a `CrawlTask`.
    """

    def __init__(self, site_id, url):
        """Initialize a crawl task.
        """
        self._site_id = site_id
        self._url = url
        self._revisit_wait = 0
        self._revisit_count = -1
        self._change_count = 0

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'site_id': self._site_id,
            'url': self._url,
            'revisit_wait': self._revisit_wait,
            'revisit_count': self._revisit_count,
            'change_count': self._change_count,
        }

    def __setstate__(self, state):
        """Use by pickle when instances are serialized.
        """
        self._site_id = state['site_id']
        self._url = state['url']
        self._revisit_wait = state['revisit_wait']
        self._revisit_count = state['revisit_count']
        self._change_count = state['change_count']

    def report_visit(self, changed):
        """Report that the directory was visited.

        The `changed` argument should be `True` if the content of the directory
        changed, `False` otherwise.  If it's the first time visited the value
        of this argument will be ignored.
        """
        if self._revisit_count >= 0 and changed:
            self._change_count += 1
        self._revisit_count += 1

    def reset_counters(self):
        """Reset counters for revisit and changes.
        """
        self._revisit_count = 0
        self._change_count = 0

    def _get_site_id(self):
        """Get method for the `site_id` property.
        """
        return self._site_id

    site_id = property(_get_site_id)

    def _get_url(self):
        """Get method for the `url` property.
        """
        return self._url

    url = property(_get_url)

    def _get_revisit_wait(self):
        """Get method for the `revisit_wait` property.
        """
        return self._revisit_wait

    def _set_revisit_wait(self, seconds):
        """Set method for the `revisit_wait` property.
        """
        self._revisit_wait = seconds

    revisit_wait = property(_get_revisit_wait, _set_revisit_wait)

    def _get_revisit_count(self):
        """Get method for the `revisit_count` property.
        """
        return self._revisit_count

    revisit_count = property(_get_revisit_count)

    def _get_change_count(self):
        """Get method for the `change_count` property.
        """
        return self._change_count

    change_count = property(_get_change_count)


class TaskQueue(object):
    """Task queue.

    Queue used to collect the crawl tasks that are going to be executed.
    """

    def __init__(self, sites_info, db_home):
        """Initializes the queue.
        """
        # Initialize the Berkeley DB environment.  This environment will
        # contain Btree databases with duplicated records (unsorted).  Records
        # in all databases uses an integer (as string) indicating when the
        # tasks should be executed.
        self._db_env = bsddb.db.DBEnv()
        self._db_env.open(db_home, bsddb.db.DB_CREATE | bsddb.db.DB_RECOVER
                          | bsddb.db.DB_INIT_TXN | bsddb.db.DB_INIT_LOG
                          | bsddb.db.DB_INIT_MPOOL | bsddb.db.DB_THREAD)
        self._key_length = len(str(sys.maxint))
        # Create the database for the sites.
        sites_db_name = 'sites.db'
        self._sites_db = bsddb.db.DB(self._db_env)
        self._sites_db.set_flags(bsddb.db.DB_DUP)
        self._sites_db.open(sites_db_name, bsddb.db.DB_BTREE,
                            bsddb.db.DB_CREATE | bsddb.db.DB_AUTO_COMMIT
                            | bsddb.db.DB_THREAD)
        # Get the list of databases to purge sites that were removed from the
        # configuration file.
        old_dbs = [os.path.basename(db_path)
                   for db_path in glob.glob('%s/*.db' % db_home.rstrip('/'))]
        old_dbs.remove(sites_db_name)
        # Open or create databases for tasks.
        self._task_dbs = {}
        for site_id, info in sites_info.iteritems():
            task_db_name = '%s.db' % site_id
            task_db = bsddb.db.DB(self._db_env)
            task_db.set_flags(bsddb.db.DB_DUP)
            task_db.open(task_db_name, bsddb.db.DB_BTREE, bsddb.db.DB_CREATE
                         | bsddb.db.DB_AUTO_COMMIT | bsddb.db.DB_THREAD)
            self._task_dbs[site_id] = task_db
            if task_db_name in old_dbs:
                old_dbs.remove(task_db_name)
                if site_id not in self._sites_db.values():
                    self._sites_db.put(self._get_key(), site_id)
            else:
                # New site added to the configuration file.
                self._sites_db.put(self._get_key(), site_id)
                self._put(CrawlTask(site_id, info['url']))
        for task_db_name in old_dbs:
            self._db_env.dbremove(task_db_name)
        self._sites_info = sites_info
        self._revisits = 5
        self._mutex = threading.Lock()

    def __len__(self):
        """Return the number of crawl tasks in the queue.
        """
        self._mutex.acquire()
        try:
            return sum(len(task_db) for task_db in self._task_dbs.itervalues())
        finally:
            self._mutex.release()

    def put_new(self, task):
        """Put a task for a new directory.

        A new directory is a directory that has not been visited.  The
        `TaskQueue` will assign a privileged priority for this task.
        """
        self._mutex.acquire()
        try:
            self._put(task)
        finally:
            self._mutex.release()

    def put_visited(self, task, changed):
        """Put a task for a visited directory.

        If the directory is visited for the first time the `changed` argument
        will be ignored.  If the directory was previously visited the `changed`
        argument should be `True` if the directory changed, `False` otherwise.
        This information will be used to estimate the change frequency.  In
        both cases the `TaskQueue` will schedule a task to revisit the
        directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            site_info = self._sites_info[site_id]
            task.report_visit(changed)
            if task.revisit_count == 0:
                # First visit.  Set default values.
                task.revisit_wait = site_info['default_revisit_wait']
                logging.info('Setting revisit frequency for "%s" to '
                             '%d seconds' % (task.url, task.revisit_wait))
            else:
                if task.revisit_count >= self._revisits:
                    minimum = site_info['min_revisit_wait']
                    maximum = site_info['max_revisit_wait']
                    estimated = self._estimate_revisit_wait(task)
                    task.revisit_wait = min(maximum, max(minimum, estimated))
                    task.reset_counters()
                    logging.info('Changing revisit frequency for "%s" to '
                                 '%d seconds' % (task.url, task.revisit_wait))
            self._put(task, task.revisit_wait)
        finally:
            self._mutex.release()

    def get(self):
        """Return an executable task.

        Return a task executable right now.  The task should be reported later
        as done or error using `report_done()` and `report_error()`.  If there
        is not executable task an `EmptyQueue` exception is raised.
        """
        self._mutex.acquire()
        try:
            if not self._sites_db:
                # Sites database is empty.
                raise EmptyQueue('No sites.')
            task = None
            txn = self._db_env.txn_begin()
            sites_cursor = self._sites_db.cursor(txn)
            site_priority, site_id = sites_cursor.first()
            while task is None:
                site_priority, site_id = sites_cursor.current()
                if site_priority > self._get_key():
                    # The site cannot be visited right now.
                    sites_cursor.close()
                    txn.commit()
                    raise EmptyQueue('No available sites.')
                try:
                    task_db = self._task_dbs[site_id]
                except KeyError:
                    # Got the ID of an old site.
                    sites_cursor.delete()
                    if not sites_cursor.next():
                        # Last site in database checked.
                        sites_cursor.close()
                        txn.commit()
                        raise EmptyQueue('No executable tasks.')
                else:
                    if not task_db:
                        # The task database is empty.
                        if not sites_cursor.next():
                            # Last site in database checked.
                            sites_cursor.close()
                            txn.commit()
                            raise EmptyQueue('No executable tasks.')
                    else:
                        task_cursor = task_db.cursor(txn)
                        task_priority, pickled_task = task_cursor.first()
                        if task_priority > self._get_key():
                            # The task at the head of the database is not
                            # executable right now.
                            if not sites_cursor.next():
                                # Last site in database checked.
                                task_cursor.close()
                                sites_cursor.close()
                                txn.commit()
                                raise EmptyQueue('No executable tasks.')
                        else:
                            # There is an executable task.
                            sites_cursor.delete()
                            task = cPickle.loads(pickled_task)
                        task_cursor.close()
            sites_cursor.close()
            txn.commit()
            return task
        finally:
            self._mutex.release()

    def report_done(self, task):
        """Report task as done.

        Report a task returned by `get()` as successfully done.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            site_info = self._sites_info[site_id]
            txn = self._db_env.txn_begin()
            site_key = self._get_key(site_info['request_wait'])
            self._sites_db.put(site_key, site_id, txn)
            task_db = self._task_dbs[site_id]
            task_cursor = task_db.cursor(txn)
            task_cursor.first()
            task_cursor.delete()
            task_cursor.close()
            txn.commit()
        finally:
            self._mutex.release()

    def report_error_site(self, task):
        """Report error executing a task.

        Report an error executing a task returned by `get()`.  Protocol
        handlers should use this method to report an error contacting a site.
        """
        self._mutex.acquire()
        try:
            # Do not remove the task from the database!
            site_id = task.site_id
            site_info = self._sites_info[site_id]
            site_key = self._get_key(site_info['error_site_wait'])
            self._sites_db.put(site_key, site_id)
        finally:
            self._mutex.release()


    def report_error_dir(self, task):
        """Report error executing a task.

        Report an error executing a task returned by `get()`.  Protocol
        handlers should use this method to report that they contacted the site
        but an error occurs retrieving the content of a directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            site_info = self._sites_info[site_id]
            txn = self._db_env.txn_begin()
            site_key = self._get_key(site_info['request_wait'])
            self._sites_db.put(site_key, site_id, txn)
            task_db = self._task_dbs[site_id]
            task_cursor = task_db.cursor(txn)
            task_cursor.first()
            task_cursor.delete()
            task_cursor.close()
            self._put(task, site_info['error_dir_wait'], txn)
            txn.commit()
        finally:
            self._mutex.release()

    def flush(self):
        """Flush to disc the modifications.
        """
        self._mutex.acquire()
        try:
            self._sites_db.sync()
            for task_db in self._task_dbs.itervalues():
                task_db.sync()
        finally:
            self._mutex.release()

    def close(self):
        """Close the queue.
        """
        self._mutex.acquire()
        try:
            self._sites_db.close()
            for task_db in self._task_dbs.itervalues():
                task_db.close()
            self._db_env.close()
        finally:
            self._mutex.release()

    def _put(self, task, seconds=0, txn=None):
        """Put a task in the queue.

        Internal method used to put a task in the queue that should be executed
        after the given number of seconds.  It is invoked by `put_new()`,
        `put_visited()` and `put_revisited()`.  The default value for the
        `seconds` argument is 0, meaning right now.
        """
        site_id = task.site_id
        task_db = self._task_dbs[site_id]
        if txn is None:
            task_db.put(self._get_key(seconds), cPickle.dumps(task, 2))
        else:
            task_db.put(self._get_key(seconds), cPickle.dumps(task, 2), txn)

    def _get_key(self, seconds=0):
        """Return a key for a site or task.

        Return an string that can be used as a key for a task that should to be
        executed after the given number of seconds.  It will use an string with
        the number of seconds since UNIX epoch.  The default value for the
        `seconds` argument is 0, meaning right now.
        """
        return str(int(time.time()) + seconds).zfill(self._key_length)

    @staticmethod
    def _estimate_revisit_wait(task):
        """Return an estimate revisit wait for the task.
        """
        # This algorithm uses the estimator proposed by Junghoo Cho (University
        # of California, LA) and Hector Garcia-Molina (Stanford University) in
        # "Estimating Frequency of Change".
        changes = task.change_count
        visits = task.revisit_count
        wait = task.revisit_wait
        if changes > 0:
            new_wait  = wait / - math.log((visits - changes + 0.5) /
                                          (visits + 0.5))
        else:
            new_wait = wait * visits
        return int(round(new_wait))
