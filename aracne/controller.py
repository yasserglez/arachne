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
from aracne.crawl import CrawlManager
from aracne.processor import ProcessorManager


class Controller(Daemon):
    """Controls the execution of the components of the application.

    Creates the `TaskQueue`, `ResultQueue`, `CrawlManager` and
    `ProcessorManager` instances.  When the `start()` method is invoked, the
    process is daemonized, starts the `CrawlManager` and the
    `ProcessorManager`.  Then, sleeps until a SIGTERM signal is received and
    stops the components.
    """

    def __init__(self, config):
        """Initializes attributes.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlManager` and
        `ProcessorManager` instances.  The `config` parameter should be a
        dictionary with the configurations of the application.
        """
        super(Controller, self).__init__(pidfile=config['general']['pidfile'],
                                         user=config['general']['user'],
                                         group=config['general']['group'])
        self._task_queue = TaskQueue(config)
        self._result_queue = ResultQueue(config)
        self._crawl_manager = CrawlManager(config, self._task_queue,
                                           self._result_queue)
        self._processor_manager = ProcessorManager(config, self._task_queue,
                                                   self._result_queue)
        self._running = False

    def run(self):
        """Starts the execution of the controller.

        Sets the running flag, starts the `CrawlManager` and the
        `ProcessorManager`, sleeps until a SIGTERM signal is received and then
        stops the components.
        """
        self._running = True
        self._crawl_manager.start()
        self._processor_manager.start()
        while self._running:
            signal.pause()
        self._crawl_manager.terminate()
        self._processor_manager.terminate()
        self._crawl_manager.join()
        self._processor_manager.join()

    def terminate(self):
        """Orders to end the application.

        Clears the running flag.
        """
        self._running = False
