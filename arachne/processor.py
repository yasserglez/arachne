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

"""Components used to process the crawl results.
"""

import time
import logging
import threading

from arachne.error import EmptyQueue
from arachne.task import CrawlTask


class ResultProcessor(object):
    """Result processor.

    Abstract class that should be subclassed by the result processors.
    Instances of subclasses are used by the `ProcessorManager`.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """

    def process(self, result):
        """Process a crawl result.

        If the result is successfully processed the handler should report the
        result as done to the `ResultQueue` using `report_done()`.  When an
        error occurs processing the result the processor should report it to
        the `ResultQueue` using `report_error()` and print a message with
        `logging.error()`.
        """
        raise NotImplementedError('A subclass must override this method.')


class NaiveProcessor(ResultProcessor):
    """Naive processor.

    This processor only will add a new task to `TaskQueue` for each directory
    entry found in the result.  This can be used to walk the entire directory
    tree.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """
        ResultProcessor.__init__(self, sites_info, index_dir, tasks, results)
        self._tasks = tasks
        self._results = results

    def process(self, result):
        """Process a crawl result.
        """
        for entry_url, data in result:
            if data['is_dir']:
                task = CrawlTask(result.task.site_id, entry_url)
                self._tasks.put_new(task)
        self._results.report_done(result)


class IndexProcessor(ResultProcessor):
    """Xapian index processor.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """
        ResultProcessor.__init__(self, sites_info, index_dir, tasks, results)

    def process(self, result):
        """Process a crawl result.
        """
        raise NotImplementedError('A subclass must override this method.')


class ProcessorManager(threading.Thread):
    """Processor manager.

    Create and feed the processor.  The processor that will be used is
    currently set in the `__init__()` method but it should be configurable in
    future versions.

    When the `start()` method is invoked it enters in a loop feeding the
    processor with results from the `ResultQueue` until the `stop()` method is
    invoked.  It runs in an independent thread of execution.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor manager.
        """
        threading.Thread.__init__(self)
        self._sleep = 1
        self._results = results
        self._processor = NaiveProcessor(sites_info, index_dir, tasks, results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.
        """
        try:
            self._running = True
            while self._running:
                try:
                    result = self._results.get()
                except EmptyQueue:
                    time.sleep(self._sleep)
                else:
                    self._process(result)
        except:
            logging.exception('Unhandled exception, printing traceback')

    def stop(self):
        """Order the main loop to end.
        """
        self._running = False

    def _process(self, result):
        """Process a crawl result.
        """
        logging.info('Processing "%s"' % result.task.url)
        self._processor.process(result)
