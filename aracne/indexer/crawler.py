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

"""`SiteCrawler` and `CrawlerManager` definitions.
"""

import time
import logging
import threading

from aracne.indexer.error import EmptyQueue
from aracne.indexer.handler import ProtocolHandler


class SiteCrawler(threading.Thread):
    """Site crawler.

    When the `start()` method is invoked it enters in a loop getting crawl
    tasks from the `TaskQueue`, executing the tasks and reporting results to
    the `ResultQueue` until the `stop()` method is invoked.  It runs in an
    independent thread of execution.
    """

    def __init__(self, sites_info, tasks, results):
        """Initialize attributes.
        """
        threading.Thread.__init__(self)
        self._tasks = tasks
        self._results = results
        self._sleep = 1
        self._handlers = {}
        for handler in ProtocolHandler.__subclasses__():
            self._handlers[handler.scheme] = handler(sites_info)
        # Flag used to stop the loop started by the run() method.
        self._running = False
        self._running_lock = threading.Lock()

    def run(self):
        """Run the main loop.

        Set the running flag and then enters a loop getting crawl tasks from
        the `TaskQueue`, executing the tasks and reporting results to the
        `ResultQueue` until the flag is cleared.
        """
        self._running_lock.acquire()
        try:
            self._running = True
            while self._running:
                self._running_lock.release()
                try:
                    task = self._tasks.get()
                except EmptyQueue:
                    time.sleep(self._sleep)
                else:
                    scheme = task.url.scheme
                    try:
                        handler = self._handlers[scheme]
                    except KeyError:
                        # Scheme it not supported.  Keep the task in the queue.
                        self._tasks.report_error(task)
                        logging.error('%s scheme is not supported.' % scheme)
                    else:
                        result = handler.execute(task)
                        if result is not None:
                            logging.info('sucess %s' % task.url)
                            self._results.put(result)
                            self._tasks.report_done(task)
                        else:
                            logging.info('error %s' % task.url)
                            self._tasks.report_error(task)
                self._running_lock.acquire()
        except:
            logging.exception('Exception raised.  Printing traceback.')
        finally:
            self._running_lock.release()

    def stop(self):
        """Order the main loop to end.

        Clear the running flag and the main loop exits.
        """
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()


class CrawlerManager(object):
    """Crawler manager.

    Create and manage the site crawlers.  It is just a way to represent the
    group of crawlers as a single component.
    """

    def __init__(self, sites_info, tasks, results, num_crawlers):
        """Initialize the site crawlers.

        Create the group of site crawlers according the the value of the
        `num_crawlers` argument.
        """
        logging.info('Crawler manager is using %d crawlers.' % num_crawlers)
        self._crawlers = [SiteCrawler(sites_info, tasks, results)
                          for i in range(num_crawlers)]

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
