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

"""`IndexerDaemon` definition.
"""

import os
import signal
import logging
import hashlib

from aracne import __version__
from aracne.utils.url import URL
from aracne.utils.daemon import Daemon
from aracne.indexer.task import TaskQueue
from aracne.indexer.result import ResultQueue
from aracne.indexer.crawler import CrawlerManager
from aracne.indexer.processor import ProcessorManager


class IndexerDaemon(Daemon):
    """Aracne indexer daemon.

    This class implements the UNIX daemon used to crawl the sites and generate
    the index.  When the `start()` method is invoked it starts the components
    and sleeps until a SIGTERM signal is received to stop the components.
    """

    def __init__(self, sites, admin_email, num_crawlers, spool_dir,
                 database_dir, log_file, log_level, pid_file, user, group):
        """Initialize the indexer daemon.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ProcessorManager` instances.  The `sites` argument should be a list
        with the information for each site.
        """
        Daemon.__init__(self, pid_file=pid_file, user=user, group=group)
        logging.basicConfig(filename=log_file, level=log_level,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Aracne indexer daemon %s.' % __version__)
        logging.info('Running with %d sites configured.' % len(sites))
        # Create URL instances and assign an id to each site.
        sites_info = {}
        for site in sites:
            site['url'] = URL(site['url'])
            sites_info[hashlib.sha1(str(site['url'])).hexdigest()] = site
        # Create or check required directories.
        results_dir = os.path.join(spool_dir, 'results')
        if not os.path.isdir(results_dir):
            os.mkdir(results_dir)
        tasks_dir = os.path.join(spool_dir, 'tasks')
        if not os.path.isdir(tasks_dir):
            os.mkdir(tasks_dir)
        index_dir = os.path.join(database_dir, 'index')
        if not os.path.isdir(index_dir):
            os.mkdir(index_dir)
        # Initialize components.
        self._tasks = TaskQueue(sites_info, tasks_dir)
        logging.info('There are %d tasks waiting for execution.'
                     % len(self._tasks))
        self._results = ResultQueue(sites_info, results_dir)
        logging.info('There are %d results waiting for processing.'
                     % len(self._results))
        self._crawlers = CrawlerManager(sites_info, admin_email, num_crawlers,
                                        self._tasks, self._results)
        self._processor = ProcessorManager(sites_info, index_dir, self._tasks,
                                           self._results)
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
