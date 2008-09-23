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

"""`CrawlTask` and related classes.
"""

import os
import time
import math
import threading

from aracne.index.error import EmptyQueueError
from aracne.utils.persist import PriorityQueue, QueueError


class CrawlTask(object):
    """Crawl task.

    This class represents an action to list the content of a directory.
    Executing a task produces a `CrawlResult`.
    """

    def __init__(self, site_id, url):
        """Initialize a crawl task.
        """
        self._site_id = site_id
        self._url = url
        self._revisit_wait = 0
        self._revisit_count = 0
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

    def report_revisit(self, changed):
        """Report that the directory was revisited.

        The `changed` argument should be set to `True` if the content of the
        directory changed, `False` otherwise.
        """
        if changed:
            self._change_count += 1
        self._revisit_count += 1

    def _get_site_id(self):
        """Get method for the `site_id` property.
        """
        return self._site_id

    def _get_url(self):
        """Get method for the `url` property.
        """
        return self._url

    def _get_revisit_wait(self):
        """Get method for the `revisit_wait` property.
        """
        return self._revisit_wait

    def _set_revisit_wait(self, seconds):
        """Set method for the `revisit_wait` property.

        This method also resets the counters for revisits and changes.
        """
        self._revisit_wait = seconds
        self._revisit_count = 0
        self._change_count = 0

    def _get_revisit_count(self):
        """Get method for the `revisit_count` property.
        """
        return self._revisit_count

    def _get_change_count(self):
        """Get method for the `change_count` property.
        """
        return self._change_count

    site_id = property(_get_site_id)

    url = property(_get_url)

    revisit_wait = property(_get_revisit_wait, _set_revisit_wait)

    revisit_count = property(_get_revisit_count)

    change_count = property(_get_change_count)


class TaskQueue(object):
    """Task queue.

    This queue is used to collect the crawl tasks waiting to be executed.
    """

    def __init__(self, dirname, sites_info):
        """Initializes the queue.
        """
        sites_filename = 'sites.db'
        self._sites = PriorityQueue(os.path.join(dirname, sites_filename))
        # Get the list files in the directory to purge old queues (sites
        # removed from the configuration file).
        old_queues = os.listdir(dirname)
        old_queues.remove(sites_filename)
        self._tasks = {}
        for site_id, info in sites_info.iteritems():
            filename = '%s.db' % site_id
            queue = PriorityQueue(os.path.join(dirname, filename))
            self._tasks[site_id] = queue
            if filename in old_queues:
                old_queues.remove(filename)
            else:
                # New site added to the configuration file.  Create a new task
                # to list the content of the root directory.
                self._sites.put(site_id, self._get_priority())
                task = CrawlTask(site_id, info['url'])
                self._tasks[site_id].put(task, self._get_priority())
        for filename in old_queues:
            os.unlink(os.path.join(dirname, filename))
        self._mutex = threading.Lock()
        self._sites_info = sites_info
        self._revisits = 5

    def __len__(self):
        """Return the number of crawl tasks in the queue.
        """
        self._mutex.acquire()
        try:
            return sum(len(queue) for queue in self._tasks.itervalues())
        finally:
            self._mutex.release()

    def put_new(self, task):
        """Put a task for a new directory.

        A new directory is a directory that has not been visited.  The
        `TaskQueue` will assign a privileged priority for this task.
        """
        self._mutex.acquire()
        try:
            self._put(task, self._get_priority())
        finally:
            self._mutex.release()

    def put_visited(self, task):
        """Put a task for a visited directory.

        A visited directory is a directory visited for first time.  The
        `TaskQueue` will schedule a task to revisit the directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            revisit_wait = self._sites_info[site_id]['default_revisit_wait']
            task.revisit_wait =  revisit_wait
            self._put(task, self._get_priority(task.revisit_wait))
        finally:
            self._mutex.release()

    def put_revisited(self, task, changed):
        """Put a task for a revisited directory.

        A revisited directory is a directory that is already indexed and it is
        visited to check if it changed.  The `changed` argument should be
        `True` if the directory changed, `False` otherwise.  This information
        will be used to estimate the change frequency.  The `TaskQueue` will
        schedule a task to revisit the directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            task.report_revisit(changed)
            if task.revisit_count >= self._revisits:
                estimated = self._estimate_revisit_wait(task)
                minimum = self._sites_info[site_id]['min_revisit_wait']
                maximum = self._sites_info[sites_id]['max_revisit_wait']
                task.revisit_wait = min(maximum, max(minimum, estimated))
            self._put(task, self._get_priority(task.revisit_wait))
        finally:
            self._mutex.release()

    def get(self):
        """Return an executable task.

        Return a task executable right now.  The task should be reported later
        as done or error using `report_done()` and `report_error()`.  If there
        is not executable task an `EmptyQueueError` exception is raised.
        """
        self._mutex.acquire()
        try:
            # Sites that can be visited but do not have executable tasks should
            # be temporally removed from the sites queue and inserted again
            # when an executable task is found.
            sites_without_tasks = []
            while True:
                try:
                    site_id, site_priority = self._sites.head()
                except QueueError:
                    # Empty queue.  Running without sites?
                    raise EmptyQueueError()
                else:
                    if site_priority > self._get_priority():
                        # The site at the head of the queue cannot be visited
                        # right now.  Then, the queue is empty.
                        raise EmptyQueueError()
                    else:
                        try:
                            task, task_priority = self._tasks[site_id].head()
                        except KeyError:
                            # The head of the sites queue is an old site.
                            self._sites.get()
                        except QueueError:
                            # The task queue is empty.
                            sites_without_tasks.append(self._sites.get())
                        else:
                            if task_priority > self._get_priority():
                                # The task at the head of the queue is not
                                # executable right now.
                                sites_without_tasks.append(self._sites.get())
                            else:
                                # Executable task.
                                self._sites.get()
                                return task
        finally:
            for site_id, site_priority in sites_without_tasks:
                self._sites.put(site_id, site_priority)
            self._mutex.release()

    def report_done(self, task):
        """Report task as done.

        Report a task returned by `get()` as successfully done.  The `TaskQueue`
        will guaranty that the site will not be visited until the time of
        request wait is elapsed.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            self._tasks[site_id].get()
            request_wait = self._sites_info[site_id]['request_wait']
            self._sites.put(site_id, self._get_priority(request_wait))
        finally:
            self._mutex.release()

    def report_error(self, task):
        """Report an error executing a task.

        Report an error executing a task returned by `get()`.  This usually
        means that the site was unreachable.  The `TaskQueue` should wait a
        time longer than the request wait before allowing contact the site
        again.
        """
        self._mutex.acquire()
        try:
            # Do not remove the task from the queue!
            site_id = task.site_id
            error_wait = self._sites_info[site_id]['error_wait']
            self._sites.put(site_id, self._get_priority(error_wait))
        finally:
            self._mutex.release()

    def sync(self):
        """Synchronize the queue on disk.
        """
        self._mutex.acquire()
        try:
            self._sites.sync()
            for queue in self._tasks.itervalues():
                queue.sync()
        finally:
            self._mutex.release()

    def close(self):
        """Close the queue.
        """
        self._mutex.acquire()
        try:
            self._sites.close()
            for queue in self._tasks.itervalues():
                queue.close()
        finally:
            self._mutex.release()

    def _put(self, task, priority):
        """Put a task in the queue.

        Internal method used to put a task in the queue.  It is invoked by
        `put_new()`, `put_visited()` and `put_revisited()` with the right
        priority for the task.
        """
        self._tasks[task.site_id].put(task, priority)

    @staticmethod
    def _get_priority(seconds=0):
        """Return a priority value.

        Return an integer value (seconds since UNIX epoch) that can be used as
        priority for a task that needs to be executed after `seconds` seconds.
        The default value for the `seconds` argument is 0, meaning right now.
        """
        return int(time.time()) + seconds

    @staticmethod
    def _estimate_revisit_wait(task):
        """Return an estimate revisit wait for the task.
        """
        # This algorithm uses the estimator proposed by Junghoo Cho (University
        # of California, LA) and Hector Garcia-Molina (Stanford University) in
        # "Estimating Frequency of Change".
        c = task.change_count if task.change_count else 1
        w = task.revisit_wait
        v = task.revisit_count
        nw = w / (- math.log((v - c + 0.5) / (v + 0.5)))
        return int(math.ceil(nw) if nw >= (math.floor(nw) + 0.5)
                   else math.floor(nw))
