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

import os
import signal
import logging
import hashlib

from aracne.util.url import URL
from aracne.util.daemon import Daemon
from aracne.task import TaskQueue
from aracne.result import ResultQueue
from aracne.crawler import CrawlerManager
from aracne.processor import ProcessorManager


__author__ = 'Yasser González Fernández <yglez@uh.cu>'
__copyright__ = 'Copyright (C) 2008 Yasser González Fernández'
__version__ = '0.1.0'


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
        # Initialize logs.
        logging.basicConfig(filename=config['logfile'],
                            level=config['loglevel'],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting aracned (Aracne) %s.' % __version__)
        logging.info('Running with %d configured sites.' % len(sites))
        # Create URL instances and site ids.
        for site in sites:
            site['siteid'] = hashlib.sha1(site['url']).hexdigest()
            site['url'] = URL(site['url'])
        logging.debug('Initializing components of the daemon.')
        # Create required directories.
        resultsdir = os.path.join(config['spooldir'], 'results')
        if not os.path.isdir(resultsdir):
            os.mkdir(resultsdir)
        tasksdir = os.path.join(config['spooldir'], 'tasks')
        if not os.path.isdir(tasksdir):
            os.mkdir(tasksdir)
        # Initialize components.
        self._tasks = TaskQueue(sites)
        self._results = ResultQueue(resultsdir, sites)
        self._crawlers = CrawlerManager(config['numcrawlers'], self._tasks,
                                        self._results)
        self._processor = ProcessorManager(self._tasks, self._results)
        # Flag used to stop the loop started by the run() method.
        self._running = False
        logging.debug('Components of the daemon initialized.')

    def run(self):
        """Run the main loop.

        Override the `run()` method from the `Daemon` class.  Set the running
        flag, start the components and then sleep until a SIGTERM signal is
        received to stop the components.
        """
        self._running = True
        logging.debug('Starting components of the daemon.')
        self._crawlers.start()
        self._processor.start()
        logging.debug('Entering main loop of the daemon.')
        while self._running:
            signal.pause()
        logging.debug('Main loop of the daemon exited.  Stopping components.')
        self._crawlers.stop()
        self._processor.stop()
        self._crawlers.join()
        self._processor.join()
        self._results.close()
        logging.debug('Components of the daemon stopped.')
        logging.info('Daemon stopped.  Exiting.')
        logging.shutdown()

    def terminate(self):
        """Order the main loop to end.

        Override the `terminate()` method from the `Daemon` class.  Clear the
        running flag and the main loop should exit.
        """
        self._running = False
