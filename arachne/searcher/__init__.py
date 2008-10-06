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

"""Subpackage with classes related with the searcher daemon.
"""

import signal
import logging

from arachne import __version__
from arachne.util.daemon import Daemon


class SearcherDaemon(Daemon):
    """Searcher daemon.

    This class implements the UNIX daemon used to process and return the
    responses of the queries to the database.
    """

    def __init__(self, sites, database_dir, log_file, log_level, pid_file,
                 user, group):
        """Initialize the searcher daemon.
        """
        Daemon.__init__(self, pid_file=pid_file, user=user, group=group)
        logging.basicConfig(filename=log_file, level=log_level,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info('Starting Arachne searcher daemon %s' % __version__)
        logging.info('Running with %d sites configured' % len(sites))
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.
        """
        try:
            self._running = True
            while self._running:
                signal.pause()
            logging.info('Daemon stopped, exiting')
        except:
            logging.exception('Unhandled exception, printing traceback')
        finally:
            logging.shutdown()

    def terminate(self):
        """Order the main loop to end.
        """
        self._running = False
