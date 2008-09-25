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

"""Subpackage with classes related with the query daemon.
"""

import signal
import logging

from aracne import __version__
from aracne.utils.daemon import Daemon


class QueryDaemon(Daemon):
    """Aracne query daemon.

    This class implements the UNIX daemon used to process the querys to the
    database.
    """

    def __init__(self, config, sites):
        """Initialize query daemon.
        """
        Daemon.__init__(self, pid_file=config['pid_file'], user=config['user'],
                        group=config['group'])
        # Initialize logs.
        logging.basicConfig(filename=config['log_file'],
                            level=config['log_level'],
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Aracne query daemon %s.' % __version__)
        logging.info('Running with %d configured sites.' % len(sites))
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.

        Override the `run()` method from the `Daemon` class.
        """
        self._running = True
        while self._running:
            signal.pause()
        logging.info('Daemon stopped.  Exiting.')
        logging.shutdown()

    def terminate(self):
        """Order the main loop to end.

        Override the `terminate()` method from the `Daemon` class.  Clear the
        running flag and the main loop should exit.
        """
        self._running = False
