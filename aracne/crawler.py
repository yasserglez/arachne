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

    def __init__(self, config, tasks, results):
        """Initializes instance attributes.
        """
        threading.Thread.__init__(self)
        self._config = config
        self._tasks = tasks
        self._results = results
        # Flag used to stop the loop started by the run() method.
        self._running = False
        self._running_lock = threading.Lock()
        # TODO: Create the protocol handlers.

    def run(self):
        """Runs the main loop.

        Sets the running flag and then enters a loop getting crawl tasks
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
                time.sleep(self._config['sleep'])
            else:
                self._execute(task)
            self._running_lock.acquire()
        self._running_lock.release()

    def stop(self):
        """Orders the main loop to end.

        Clears the running flag and the main loop exits.
        """
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()

    def _execute(self, taks):
        """Executes a crawl task.

        Executes the crawl task (`CrawlTask`) received as argument.  Reports
        error or success to the `TaskQueue` and the crawl result
        (`CrawlResult`) to the `ResultQueue`.
        """
        # TODO: Execute the crawl task.


class CrawlerManager(object):
    """Crawler manager.

    Creates and manages a number of site crawlers (`SiteCrawler`).  It is just
    a way to represent the group of crawlers as a single component.
    """

    def __init__(self, config, tasks, results):
        """Initializes the site crawlers.

        Creates the group of site crawlers (`SiteCrawler`) according the the
        value set in the configuration.
        """
        self._crawlers = [SiteCrawler(config, tasks, results)
                          for i in range(config['numcrawlers'])]

    def start(self):
        """Starts the site crawlers (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.start()

    def stop(self):
        """Stops the site crawlers (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.stop()

    def join(self):
        """Waits until the site crawlers terminates.

        Invokes the `join()` method of each one of the site crawlers
        (`SiteCrawler`).
        """
        for crawler in self._crawlers:
            crawler.join()
