# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009, 2010 Yasser González Fernández <ygonzalezfernandez@gmail.com>
# Copyright (C) 2008, 2009, 2010 Ariel Hernández Amador <gnuaha7@gmail.com>
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

"""Components related with the crawling process.
"""

import time
import logging
import threading

from arachne.error import EmptyQueue
from arachne.handler import ProtocolHandler


class SiteCrawler(threading.Thread):
    """Site crawler.

    When the `start()` method is invoked it enters in a loop getting crawl
    tasks from the task queue, executing the tasks and reporting results to the
    result queue until the `stop()` method is invoked.  It runs in an
    independent thread of execution.
    """

    def __init__(self, sites_info, tasks, results):
        """Initialize attributes.
        """
        threading.Thread.__init__(self)
        self._sleep = 1
        self._sites_info = sites_info
        self._tasks = tasks
        self._results = results
        self._handlers = {}
        for handler_class in ProtocolHandler.__subclasses__():
            handler = handler_class(sites_info, tasks, results)
            self._handlers[handler_class.name] = handler
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
            logging.exception('Unhandled exception, printing traceback')

    def stop(self):
        """Order the main loop to end.
        """
        self._running = False

    def _execute(self, task):
        """Execute a crawl task.

        Call the handler to execute the crawl task.
        """
        site_info = self._sites_info[task.site_id]
        handler_name = site_info.get('handler', task.url.scheme)
        try:
            handler = self._handlers[handler_name]
        except KeyError:
            self._tasks.report_error_site(task)
            logging.error('Could not find a handler for "%s"' % handler_name)
        else:
            if task.revisit_count == -1:
                logging.info('Visiting "%s"' % task.url)
            else:
                logging.info('Revisiting "%s"' % task.url)
            handler.execute(task)


class CrawlerManager(object):
    """Crawler manager.

    Create and manage the site crawlers.  It is just a way to represent the
    group of crawlers as a single component.
    """

    def __init__(self, sites_info, num_crawlers, tasks, results):
        """Initialize the site crawlers.

        Create a group of site crawlers according the the value of the
        `num_crawlers` argument.
        """
        self._crawlers = [SiteCrawler(sites_info, tasks, results)
                          for i in range(num_crawlers)]
        if num_crawlers > 0:
            logging.info('Using %d site crawlers' % num_crawlers)
        else:
            logging.info('Running without site crawlers')

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
