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

import threading

from aracne.errors import EmptyQueueError


class ResultProcessor(object):
    """Crawl result processor.

    An instance of this class will be used to process each one of the crawl
    results from the `ResultQueue`.
    """

    def __init__(self, task_queue, result_queue):
        """Initialize instances.

        The `ProcessorManager` will create an instance of this class providing
        the `TaskQueue` and the `ResultQueue` as arguments.
        """
        self._task_queue = task_queue
        self._result_queue = result_queue

    def process(self, result):
        """Process the crawl result.
        """


class ProcessorManager(threading.Thread):
    """Processor manager.

    Creates, manages and feeds the `ResultProcessor` with the results
    (`CrawlResult`) received from the `ResultQueue`.  It runs in an independent
    thread of execution.
    """

    def __init__(self, config, task_queue, result_queue):
        """Initializes attributes.
        """
        threading.Thread.__init__(self)
        self._processor = ResultProcessor(task_queue, result_queue)
        self._sleep_time = config['processormanager']['sleeptime']
        self._task_queue = task_queue
        self._result_queue = result_queue
        self._running = False
        self._running_lock = threading.Lock()

    def run(self):
        """Runs the processor manager.

        Sets the running flag and then enters a loop processing the results
        (`CrawlResults`) until the flag is cleared.
        """
        self._running_lock.acquire()
        self._running = True
        while self._running:
            self._running_lock.release()
            try:
                # Try to get a crawl result to be processed.  Wait a few
                # seconds for an item if not available right now.
                result = self._result_queue.get(timeout=self._sleep_time)
            except EmptyQueueError:
                # Crawl result not available.  Check the running flag and if
                # not cleared try to get another crawl result.
                pass
            else:
                # Crawl result available.
                self._processor.process(result)
            self._running_lock.acquire()
        self._running_lock.release()

    def terminate(self):
        """Terminates the thread execution.

        Clears the running flag and then the main loop is exited.
        """
        self._running_lock.acquire()
        self._running = False
        self._running_lock.release()
