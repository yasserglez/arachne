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

"""`SiteCrawler` and `CrawlerManager`.
"""

import time
import logging
import threading

from arachne.indexer.error import EmptyQueue
from arachne.indexer.handler import ProtocolHandler


class SiteCrawler(threading.Thread):
    """Site crawler.

    When the `start()` method is invoked it enters in a loop getting crawl
    tasks from the task queue, executing the tasks and reporting results to the
    result queue until the `stop()` method is invoked.  It runs in an
    independent thread of execution.
    """

    def __init__(self, sites_info, admin_email, tasks, results):
        """Initialize attributes.
        """
        threading.Thread.__init__(self)
        self._sleep = 1
        self._tasks = tasks
        self._results = results
        self._handlers = {}
        for handler in ProtocolHandler.__subclasses__():
            self._handlers[handler.scheme] = handler(sites_info, admin_email)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.
        """
        try:
            self._running = True
            while self._running:
                try:
                    task = self._tasks.get()
                except EmptyQueue:
                    time.sleep(self._sleep)
                else:
                    self._execute(task)
        except:
            logging.exception('Exception raised.  Printing traceback.')

    def stop(self):
        """Order the main loop to end.
        """
        self._running = False

    def _execute(self, task):
        """Execute a crawl task.

        Call the handler to execute the crawl task and report the result to the
        result queue.
        """
        scheme = task.url.scheme
        try:
            handler = self._handlers[scheme]
        except KeyError:
            self._tasks.report_error(task)
            logging.error('The %s scheme is not supported.' % scheme)
        else:
            result = handler.execute(task)
            if result is not None:
                self._results.put(result)
                self._tasks.report_done(task)
                logging.info('Successfully visited %s.' % task.url)
            else:
                self._tasks.report_error(task)
                logging.error('An error occurred visiting %s.' % task.url)


class CrawlerManager(object):
    """Crawler manager.

    Create and manage the site crawlers.  It is just a way to represent the
    group of crawlers as a single component.
    """

    def __init__(self, sites_info, admin_email, num_crawlers, tasks, results):
        """Initialize the site crawlers.

        Create a group of site crawlers according the the value of the
        `num_crawlers` argument.
        """
        self._crawlers = []
        for i in xrange(num_crawlers):
            crawler = SiteCrawler(sites_info, admin_email, tasks, results)
            self._crawlers.append(crawler)
        logging.info('Using %d site crawlers.' % num_crawlers)

    def start(self):
        """Start the site crawlers.
        """
        for crawler in self._crawlers:
            crawler.start()

    def stop(self):
        """Stop the site crawlers.
        """
        for crawler in self._crawlers:
            crawler.stop()

    def join(self):
        """Wait until the site crawlers terminates.

        Invoke the `join()` method of each one of the site crawlers.
        """
        for crawler in self._crawlers:
            crawler.join()
