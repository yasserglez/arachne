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

from aracne.errors import EmptyQueueError


class CrawlTask(object):
    """Crawl task.

    Represents the action of retrieving the list of files and directories found
    inside of a given directory in a site.  The result of executing this task
    is a `CrawlResult`.
    """


class TaskQueue(object):
    """Task queue.

    Collects and organizes the crawl tasks (`CrawlTask`) waiting to be
    executed.
    """

    def __init__(self, sites):
        """Initializes the queue.
        """

    def put_new(self, task):
        """Enqueue the task as new.

        Puts the task (`CrawlTask`) received as argument in the queue as a new
        task.  A new task is a task to list a directory seen for first time.
        The `TaskQueue` should assign a privileged priority to this task.
        """

    def put_changed(self, task):
        """Enqueue the task as changed.

        Puts the task (`CrawlTask`) received as argument in the queue as a
        changed task.  A changed task is a task to list a directory which
        content was changed since the last time visited.  Directories which
        content change more frequently should be visited first.
        """

    def put_unchanged(self, task):
        """Enqueue the task as unchanged.

        Puts the task (`CrawlTask`) received as argument in the queue as an
        unchanged task.  An unchanged task is a task to list a directory which
        content has not changed since the last time visited.
        """

    def get(self):
        """Returns the task at the top of the queue.

        Returns a task (`CrawlTask`) executable right now.  The task should be
        reported later as done or error using `report_done()` and
        `report_error()`.  If there is not executable task an `EmptyQueueError`
        exception is raised.
        """
        raise EmptyQueueError()

    def report_done(self, task):
        """Reports task as done.

        Reports a task returned by `get()` as done.
        """

    def report_error(self, task):
        """Reports an error executing a task.

        Reports an error executing a task returned by `get()`.  This usually
        means that the site was unreachable.  The `TaskQueue` should reschedule
        the execution of the task.
        """

    def _put(self, task, priority):
        """Puts a task in the queue.

        Internal method used to put a task in the queue.  It is invoked by
        `put_new()`, `put_changed()` and `put_unchanged()` with the right
        priority for the task.
        """

    def _report(self, task, priority):
        """Puts a site back in the queue.

        Internal method used to put the site of a task back in the queue of
        sites.  It is invoked by `report_done()` and `report_error()` with the
        right priority for the site.
        """
