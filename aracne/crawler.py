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


class SiteCrawler(object):
    """Site crawler.

    Executes each one of the crawl tasks (`CrawlTask`) received from the
    `CrawlerManager` and returns a `CrawlResult` instance.  It does the real
    work crawling a site: contact the site and retrieve the list of files and
    directories found inside the given directory.  It runs in an independent
    thread of execution.
    """


class CrawlerManager(threading.Thread):
    """Crawl manager.

    Creates, manages and feeds a configurable number of crawl workers
    (`SiteCrawler`) with crawl tasks (`CrawlTask`) received from the
    `TaskQueue` and reports the results (`CrawlResult`) to the `ResultQueue`.
    It runs in an independent thread of execution.
    """

    def __init__(self, config, task_queue, result_queue):
        """Initializes attributes.
        """
        threading.Thread.__init__(self)
        self._task_queue = task_queue
        self._result_queue = result_queue
        self._sleep_time = config['crawlmanager']['sleeptime']
        self._running = False
        self._running_lock = threading.Lock()

    def run(self):
        """Runs the crawl manager.

        Sets the running flag and then enters a loop processing the crawl tasks
        (`CrawlTask`) and reporting the results (`CrawlResult`) until the flag
        is cleared.
        """
        self._running_lock.acquire()
        self._running = True
        while self._running:
            self._running_lock.release()
            # TODO: Substitute this time.sleep() call with the code to get the
            # crawl task, process it and the report the result.
            time.sleep(self._sleep_time)
            self._running_lock.acquire()
        self._running_lock.release()

    def terminate(self):
        """Terminates thread execution.

        Clears the running flag and then the main loop is exited.
        """
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()
