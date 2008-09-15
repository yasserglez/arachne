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
import time
import threading

from aracne.errors import EmptyQueueError
from aracne.utils.persist import PriorityQueue, QueueError


class CrawlTask(object):
    """Crawl task.

    It represents the action of retrieving the list of files and directories
    found inside a given directory.  Executing a task produces a `CrawlResult`.

    The `update_wait` (number of seconds to wait before updating the content of
    the directory), `update_count` (number of updates with the set
    `update_wait`) and `change_count` (number of updates where changes were
    detected) attributes are used by the `TaskQueue`.  The `TaskQueue` modifies
    this values using the `report_update()` and `set_update_wait()` methods.
    """

    siteid = property(lambda self: self._siteid)

    url = property(lambda self: self._url)

    update_wait = property(lambda self: self._update_wait)

    update_count = property(lambda self: self._update_count)

    change_count = property(lambda self: self._change_count)

    def __init__(self, siteid, url):
        """Initialize a crawl task.

        Create a new task to list a directory (pointed by `url`) in the site
        identified by `siteid`.
        """
        self._siteid = siteid
        self._url = url
        self._update_wait = 0
        self._update_count = 0
        self._change_count = 0

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'siteid': self._siteid,
            'url': self._url,
            'update_wait': self._update_wait,
            'update_count': self._update_count,
            'change_count': self._change_count,
        }

    def __setstate__(self, state):
        """Use by pickle when instances are serialized.
        """
        self._siteid = state['siteid']
        self._url = state['url']
        self._update_wait = state['update_wait']
        self._update_count = state['update_count']
        self._change_count = state['change_count']

    def report_update(self, changed):
        """Report an update made to the directory.

        The `changed` argument should be a boolean value indicating if the
        content of the directory changed in this update.
        """
        self._update_count += 1
        if changed:
            self._change_count += 1

    def set_update_wait(self, value):
        """Modify the update interval.

        Set the number of seconds to wait between updates to `value`.  This
        method also resets the counters for updates and changes.
        """
        self._update_wait = value
        self._update_count = 0
        self._change_count = 0


class TaskQueue(object):
    """Task queue.

    It collects the crawl tasks waiting to be executed.
    """

    def __init__(self, dirname, sites):
        """Initializes the queue.
        """
        # Open or create the queues.
        sitedbname = 'sites.db'
        self._sitesdb = PriorityQueue(os.path.join(dirname, sitedbname))
        self._taskdb = {}
        for site in sites:
            queuefile = os.path.join(dirname, '%s.db' % site['siteid'])
            isnewsite = not os.path.isfile(queuefile)
            self._taskdb[site['siteid']] = PriorityQueue(queuefile)
            if isnewsite:
                # This is a new site added to the configuration file.
                self._sitesdb.put(site['siteid'], self._get_priority())
                task = CrawlTask(site['siteid'], site['url'])
                self._taskdb[task.siteid].put(task, self._get_priority())
        # Remove old queues.
        oldqueues = os.listdir(dirname)
        oldqueues.remove(sitedbname)
        for site in sites:
            queuename = '%s.db' % site['siteid']
            oldqueues.remove(queuename)
        for filename in oldqueues:
            os.unlink(os.path.join(dirname, filename))
        # Initialize other attributes.
        self._mutex = threading.Lock()
        self._sites = sites
        # Set the number of update visits to make before estimating a new value
        # for the change frequency of a directory.
        self._update_visits = 5

    def __len__(self):
        """Return the number of crawl results in the queue.
        """
        return sum(len(taskdb) for taskdb in self._taskdb.itervalues())

    def put_new(self, task):
        """Put a task as new.

        Put the task received as argument in the queue as a new task.  A new
        task is a task to list a directory that is not yet indexed.  The
        `TaskQueue` should assign a privileged priority for this task.
        """
        self._mutex.acquire()
        self._put(task, self._get_priority())
        self._mutex.release()

    def put_visited(self, task):
        """Put a task for a first visited directory.

        A first visited directory is a directory that was indexed and the
        `TaskQueue` schedule a task to update the content.
        """
        self._mutex.acquire()
        update_wait = self._sites[task.siteid]['defaultupdatewait']
        task.set_update_wait(update_wait)
        self._put(task, self._get_priority(task.update_wait))
        self._mutex.release()

    def put_changed(self, task):
        """Put a task as changed.

        Put the task received as argument in the queue as a changed task.  A
        changed task is a task to list a directory which content changed since
        last time visited.  This information will be used to estimate the
        change frequency.
        """
        self._mutex.acquire()
        task.report_update(True)
        if task.update_count >= self._update_visits:
            min_update_wait = self._sites[task.siteid]['minupdatewait']
            new_update_wait = self._get_update_wait(task)
            task.set_update_wait(max(new_update_wait, min_update_wait))
        self._put(task, self._get_priority(task.update_wait))
        self._mutex.release()

    def put_unchanged(self, task):
        """Put a task as unchanged.

        Put the task received as argument in the queue as an unchanged task.
        An unchanged task is a task to list a directory which content has not
        changed since the last time visited.  This information will be used to
        estimate the change frequency.
        """
        self._mutex.acquire()
        task.report_update(False)
        if task.update_count >= self._update_visits:
            min_update_wait = self._sites[task.siteid]['minupdatewait']
            new_update_wait = self._get_update_wait(task)
            task.set_update_wait(max(new_update_wait, min_update_wait))
        self._put(task, self._get_priority(task.update_wait))
        self._mutex.release()

    def get(self):
        """Returns the task at the top of the queue.

        Returns a task (`CrawlTask`) executable right now.  The task should be
        reported later as done or error using `report_done()` and
        `report_error()`.  If there is not executable task an `EmptyQueueError`
        exception is raised.
        """
        self._mutex.acquire()
        tmpsites = []
        try:
            while True:
                try:
                    siteid, priority = self._sitesdb.head()
                except QueueError:
                    # Empty queue.  Running without configured sites?
                    raise EmptyQueueError()
                else:
                    if priority > self._get_priority():
                        # The site at the head of the queue is not visitable
                        # rigt now.  No task available.
                        raise EmptyQueueError()
                    else:
                        try:
                            task, priority = self._taskdb[siteid].head()
                        except KeyError:
                            # The head of the sites db is the id of an old
                            # site.  Remove the id of the site from the
                            # database and try to get another.
                            self._sitesdb.get()
                        except QueueError:
                            # The task queue for the site is empty.
                            tmpsites.append(self._sitesdb.get())
                        else:
                            if priority > self._get_priority():
                                # The task at the head of the queue cannot be
                                # visited.
                                tmpsites.append(self._sitesdb.get())
                            else:
                                # Remove the site from the queue and return the
                                # task.
                                self._sitesdb.get()
                                return task
        finally:
            for siteid, priority in tmpsites:
                self._sitesdb.put(siteid, priority)
            self._mutex.release()

    def report_done(self, task):
        """Report task as done.

        Report a task returned by `get()` as successfuly done.
        """
        self._mutex.acquire()
        # Remove the task from the head of the queue.
        self._taskdb[task.siteid].get()
        priority = self._get_priority(self._sites[task.siteid]['requestwait'])
        self._sitesdb.put(task.siteid, priority)
        self._mutex.release()

    def report_error(self, task):
        """Reports an error executing a task.

        Reports an error executing a task returned by `get()`.  This usually
        means that the site was unreachable.  The `TaskQueue` should reschedule
        the execution of the task.
        """
        self._mutex.acquire()
        priority = self._get_priority(self._sites[task.siteid]['errorwait'])
        self._sitesdb.put(task.siteid, priority)
        self._mutex.release()

    def sync(self):
        """Synchronize the databases on disk.
        """
        self._mutex.acquire()
        self._sitesdb.sync()
        for taskdb in self._taskdb.itervalues():
            taskdb.sync()
        self._mutex.release()

    def close(self):
        """Close the databases.
        """
        self._mutex.acquire()
        self._sitesdb.close()
        for taskdb in self._taskdb.itervalues():
            taskdb.close()
        self._mutex.release()

    def _get_priority(self, secs=0):
        """Return a priority value.

        Return an integer value (seconds since UNIX epoch) that can be used as
        priority for a task that needs to be executed `secs` seconds in the
        future.  The default value for `secs` is 0, meaning right now.
        """
        return int(time.time()) + secs

    def _get_update_wait(self, task):
        """Return the change frequency of a directory.

        Estimate and return the change frequency of the directory of the task.
        """
        return task.update_wait

    def _put(self, task, priority):
        """Put a task in the queue.

        Internal method used to put a task in the queue.  It is invoked by
        `put_new()`, `put_changed()` and `put_unchanged()` with the right
        priority for the task.
        """
        self._taskdb[task.siteid].put(task)
