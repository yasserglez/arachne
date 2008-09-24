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

"""`ResultProcessor` definition.
"""

import time
import logging
import threading

from aracne.index.error import EmptyQueueError


class ResultProcessor(threading.Thread):
    """Result processor.

    When the `start()` method is invoked it enters in a loop processing crawl
    results from the `ResultQueue` until the `stop()` method is invoked.  Here
    is where the index is created.  It runs in an independent thread of
    execution.
    """

    def __init__(self, tasks, results):
        """Initialize the result processor.
        """
        threading.Thread.__init__(self)
        self._tasks = tasks
        self._results = results
        self._sleep = 3
        # Flag used to stop the loop started by the run() method.
        self._running = False
        self._running_lock = threading.Lock()

    def run(self):
        """Run the main loop.

        Set the running flag and then enter in a loop processing crawl results
        until the flag is cleared.
        """
        self._running_lock.acquire()
        try:
            self._running = True
            while self._running:
                self._running_lock.release()
                try:
                    # Try to get a crawl result to process.  If there is not
                    # result available the thread should sleep.
                    result = self._results.get()
                except EmptyQueueError:
                    time.sleep(self._sleep)
                else:
                    self._process(result)
                    self._results.report_done(result)
                self._running_lock.acquire()
        finally:
            self._running_lock.release()

    def stop(self):
        """Order the main loop to end.

        Clear the running flag and the main loop exits.
        """
        self._running_lock.acquire()
        try:
            self._running = False
        finally:
            self._running_lock.release()

    def _process(self, result):
        """Process a crawl result.
        """
