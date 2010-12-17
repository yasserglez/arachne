# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009, 2010 Yasser González Fernández <ygonzalezfernandez@gmail.com>
# Copyright (C) 2008, 2009, 2010 Ariel Hernández Amador <gnuaha7@gmail.com>
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

"""UNIX daemon of the Arachne file search engine.
"""

import os
import hashlib
import logging
import signal

from arachne import __version__
from arachne.crawler import CrawlerManager
from arachne.processor import ProcessorManager
from arachne.result import ResultQueue
from arachne.task import TaskQueue
from arachne.url import URL
from arachne.util.daemon import Daemon


class ArachneDaemon(Daemon):
    """Arachne UNIX daemon.

    This class implements the UNIX daemon used to crawl the sites and generate
    the index.  When the `start()` method is invoked it starts the components
    and sleeps until a SIGTERM signal is received to stop the components.
    """

    def __init__(self, sites, num_crawlers, spool_dir, database_dir, log_file,
                 log_level, pid_file):
        """Initialize the daemon.

        Creates the `TaskQueue`, `ResultQueue`, `CrawlerManager` and
        `ProcessorManager` instances.  The `sites` argument should be a list
        with the information for each site.
        """
        Daemon.__init__(self, pid_file=pid_file)
        logging.basicConfig(filename=log_file, level=log_level,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Arachne daemon %s' % __version__)
        logging.info('Running for %d sites' % len(sites))
        # Create URL instances and assign an id to each site.
        self._sites_info = {}
        for site in sites:
            site['url'] = URL(site['url'], True)
            self._sites_info[hashlib.sha1(str(site['url'])).hexdigest()] = site
        # Create or check required directories.
        self._results_dir = os.path.join(spool_dir, 'results')
        if not os.path.isdir(self._results_dir):
            os.mkdir(self._results_dir)
        self._tasks_dir = os.path.join(spool_dir, 'tasks')
        if not os.path.isdir(self._tasks_dir):
            os.mkdir(self._tasks_dir)
        self._database_dir = database_dir
        self._num_crawlers = num_crawlers
        self._running = False

    def run(self):
        """Run the main loop.
        """
        try:
            self._running = True
            # Initialize components.
            tasks = TaskQueue(self._sites_info, self._tasks_dir)
            logging.info('There are %d tasks waiting for execution'
                         % len(tasks))
            results = ResultQueue(self._sites_info, self._results_dir)
            logging.info('There are %d results waiting for processing'
                         % len(results))
            crawlers = CrawlerManager(self._sites_info, self._num_crawlers,
                                      tasks, results)
            processor = ProcessorManager(self._sites_info, self._database_dir,
                                         tasks, results)
            # Start components.
            crawlers.start()
            processor.start()
            # Run the main loop.
            while self._running:
                signal.pause()
            # Stop and close components.
            crawlers.stop()
            processor.stop()
            crawlers.join()
            processor.join()
            results.close()
            tasks.close()
            logging.info('Daemon stopped, exiting')
        except:
            logging.exception('Unhandled exception, printing traceback')
        finally:
            logging.shutdown()

    def terminate(self):
        """Order the main loop to end.
        """
        self._running = False
