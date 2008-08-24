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

import time
import threading

from aracne.errors import EmptyQueueError


class SiteCrawler(threading.Thread):
    """Site crawler.

    When the `start()` method is invoked it enters in a loop getting crawl
    tasks (`CrawlTask`) from the `TaskQueue`, executing the tasks and reporting
    results to the `ResultQueue` until the `stop()` method is invoked.  It runs
    in an independent thread of execution.
    """

    def __init__(self, tasks, results):
        """Initialize attributes.
        """
        threading.Thread.__init__(self)
        self._tasks = tasks
        self._results = results
        self._sleep = 5
        # Flag used to stop the loop started by the run() method.
        self._running = False
        self._running_lock = threading.Lock()
        # TODO: Create the protocol handlers.

    def run(self):
        """Run the main loop.

        Set the running flag and then enters a loop getting crawl tasks
        (`CrawlTask`) from the `TaskQueue`, executing the tasks and reporting
        results (`CrawlResults`) to the `ResultQueue` until the flag is
        cleared.
        """
        self._running_lock.acquire()
        self._running = True
        while self._running:
            self._running_lock.release()
            try:
                # Try to get a crawl task to execute.  If there is not task
                # available the thread should sleep.
                task = self._tasks.get()
            except EmptyQueueError:
                time.sleep(self._sleep)
            else:
                self._execute(task)
            self._running_lock.acquire()
        self._running_lock.release()

    def stop(self):
        """Order the main loop to end.

        Clear the running flag and the main loop exits.
        """
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()

    def _execute(self, taks):
        """Execute a crawl task.

        Execute the crawl task (`CrawlTask`) received as argument.  Report
        error or success to the `TaskQueue` and the crawl result
        (`CrawlResult`) to the `ResultQueue`.
        """
        # TODO: Execute the crawl task.


class CrawlerManager(object):
    """Crawler manager.

    Create and manage a number of site crawlers (`SiteCrawler`).  It is just a
    way to represent the group of crawlers as a single component.
    """

    def __init__(self, numcrawlers, tasks, results):
        """Initialize the site crawlers.

        Create the group of site crawlers (`SiteCrawler`) according the the
        value of the `numcrawlers` argument.
        """
        self._crawlers = [SiteCrawler(tasks, results)
                          for i in range(numcrawlers)]

    def start(self):
        """Start the site crawlers (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.start()

    def stop(self):
        """Stop the site crawlers (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.stop()

    def join(self):
        """Wait until the site crawlers terminates.

        Invoke the `join()` method of each one of the site crawlers
        (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.join()
