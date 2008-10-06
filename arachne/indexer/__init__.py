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

"""Subpackage with classes related with the indexer daemon.
"""

import os
import signal
import logging
import hashlib

from arachne import __version__
from arachne.util.url import URL
from arachne.util.daemon import Daemon
from arachne.indexer.task import TaskQueue
from arachne.indexer.result import ResultQueue
from arachne.indexer.crawler import CrawlerManager
from arachne.indexer.processor import ProcessorManager


class IndexerDaemon(Daemon):
    """Indexer daemon.

    This class implements the UNIX daemon used to crawl the sites and generate
    the index.  When the `start()` method is invoked it starts the components
    and sleeps until a SIGTERM signal is received to stop the components.
    """

    def __init__(self, sites, num_crawlers, spool_dir, database_dir, log_file,
                 log_level, pid_file, user, group):
        """Initialize the indexer daemon.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ProcessorManager` instances.  The `sites` argument should be a list
        with the information for each site.
        """
        Daemon.__init__(self, pid_file=pid_file, user=user, group=group)
        logging.basicConfig(filename=log_file, level=log_level,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Arachne indexer daemon %s' % __version__)
        logging.info('Running with %d sites configured' % len(sites))
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
        logging.info('There are %d tasks waiting for execution'
                     % len(self._tasks))
        self._results = ResultQueue(sites_info, results_dir)
        logging.info('There are %d results waiting for processing'
                     % len(self._results))
        self._crawlers = CrawlerManager(sites_info, num_crawlers, self._tasks,
                                        self._results)
        self._processor = ProcessorManager(sites_info, index_dir, self._tasks,
                                           self._results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.
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
            logging.info('Daemon stopped, exiting')
        except:
            logging.exception('Unhandled exception, printing traceback')
        finally:
            logging.shutdown()

    def terminate(self):
        """Order the main loop to end.
        """
        self._running = False
