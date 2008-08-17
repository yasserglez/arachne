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

import signal

from aracne.utils.daemon import Daemon
from aracne.task import TaskQueue
from aracne.result import ResultQueue
from aracne.crawler import CrawlerManager
from aracne.processor import ProcessorManager


class Controller(Daemon):
    """Controls the execution of the components.

    Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
    `ProcessorManager` instances.  When the `start()` method is invoked it
    starts the components and then sleeps until a SIGTERM signal is received to
    stop the components.  It runs in the main thread of execution.
    """

    def __init__(self, config):
        """Initializes the components.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ProcessorManager` instances.  The `config` parameter should be a
        dictionary with the configuration.
        """
        Daemon.__init__(self, pidfile=config['core']['pidfile'],
                        user=config['core']['user'],
                        group=config['core']['group'])
        sites = []
        self._tasks = TaskQueue(config['taskqueue'], sites)
        self._results = ResultQueue(config['resultqueue'], sites)
        self._crawlers = CrawlerManager(config['crawlermanager'], self._tasks,
                                        self._results)
        self._processor = ProcessorManager(config['processormanager'],
                                           self._tasks, self._results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Runs the main loop.

        Overrides the `run()` method from the `Daemon` class.  Sets the running
        flag, starts the components and then sleeps until a SIGTERM signal is
        received to stop the components.
        """
        self._running = True
        self._crawlers.start()
        self._processor.start()
        while self._running:
            signal.pause()
        self._crawlers.stop()
        self._processor.stop()
        self._crawlers.join()
        self._processor.join()

    def terminate(self):
        """Orders the main loop to end.

        Overrides the `terminate()` method from the `Daemon` class.  Clears the
        running flag and the main loop should exit.
        """
        self._running = False
