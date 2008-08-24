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


__author__ = 'Yasser González Fernández <yglez@uh.cu>'
__copyright__ = 'Copyright (C) 2008 Yasser González Fernández'
__version__ = '0.0.0'


class AracneDaemon(Daemon):
    """Aracne daemon.

    Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
    `ProcessorManager` instances.  When the `start()` method is invoked it
    starts the components, sleeps until a SIGTERM signal is received and then
    stops the components.  It runs in the main thread of execution.
    """

    def __init__(self, config, sites):
        """Initialize components.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ProcessorManager` instances.  The `config` parameter should be a
        dictionary with the configuration and `sites` a list with the
        information of each site.
        """
        Daemon.__init__(self, pidfile=config['pidfile'], user=config['user'],
                        group=config['group'])
        self._tasks = TaskQueue(sites)
        self._results = ResultQueue(sites)
        self._crawlers = CrawlerManager(config['numcrawlers'], self._tasks,
                                        self._results)
        self._processor = ProcessorManager(self._tasks, self._results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.

        Override the `run()` method from the `Daemon` class.  Set the running
        flag, start the components and then sleep until a SIGTERM signal is
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
        """Order the main loop to end.

        Override the `terminate()` method from the `Daemon` class.  Clear the
        running flag and the main loop should exit.
        """
        self._running = False
