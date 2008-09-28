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

"""Subpackage with classes related with the index daemon.
"""

import os
import signal
import logging
import hashlib

from aracne import __version__
from aracne.utils.url import URL
from aracne.utils.daemon import Daemon
from aracne.index.task import TaskQueue
from aracne.index.result import ResultQueue
from aracne.index.crawler import CrawlerManager
from aracne.index.processor import ResultProcessor


class IndexDaemon(Daemon):
    """Aracne index daemon.

    This class implements the UNIX daemon used to crawl the sites and generate
    the index.  When the `start()` method is invoked it starts the components
    and sleeps until a SIGTERM signal is received to stop the components.
    """

    def __init__(self, config, sites):
        """Initialize query daemon.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ResultProcessor` instances.  The `config` parameter should be a
        dictionary with the configuration and `sites` a list with the
        information of each site.
        """
        Daemon.__init__(self, pid_file=config['pid_file'], user=config['user'],
                        group=config['group'])
        # Initialize logs.
        logging.basicConfig(filename=config['log_file'],
                            level=config['log_level'],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Aracne index daemon %s.' % __version__)
        logging.info('Running for %d sites.' % len(sites))
        # Create URL instances and site IDs.
        sites_info = {}
        for site in sites:
            site['url'] = URL(site['url'])
            sites_info[hashlib.sha1(str(site['url'])).hexdigest()] = site
        # Create required directories.
        results_dir = os.path.join(config['spool_dir'], 'results')
        if not os.path.isdir(results_dir):
            os.mkdir(results_dir)
        tasks_dir = os.path.join(config['spool_dir'], 'tasks')
        if not os.path.isdir(tasks_dir):
            os.mkdir(tasks_dir)
        # Initialize components.
        self._tasks = TaskQueue(tasks_dir, sites_info)
        self._results = ResultQueue(results_dir, sites_info)
        self._crawlers = CrawlerManager(sites_info, self._tasks, self._results,
                                        config['number_crawlers'])
        self._processor = ResultProcessor(self._tasks, self._results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.

        Override the `run()` method from the `Daemon` class.  Set the running
        flag, start the components and then sleep until a SIGTERM signal is
        received to stop the components.
        """
        try:
            self._running = True
            self._crawlers.start()
            self._processor.start()
            while self._running:
                signal.pause()
            self._crawlers.stop()
            self._processor.stop()
            self._crawlers.join()
            self._processor.join()
            self._results.close()
            self._tasks.close()
            logging.info('Daemon stopped.  Exiting.')
        except:
            logging.exception('Exception raised.  Printing traceback.')
        finally:
            logging.shutdown()

    def terminate(self):
        """Order the main loop to end.

        Override the `terminate()` method from the `Daemon` class.  Clear the
        running flag and the main loop should exit.
        """
        self._running = False
