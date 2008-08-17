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

from aracne.errors import EmptyQueueError


class CrawlResult(object):
    """Crawl result.

    Represents and contains the result of listing the files and directories
    found inside of a given directory in a site.  It's the result of executing
    a `CrawlTask`.
    """


class ResultQueue(object):
    """Crawl result queue.

    Collects and organizes the crawl results (`CrawlResult`) waiting to be
    processed.
    """

    def __init__(self, config, sites):
        """Initializes the queue.
        """

    def put(self, result):
        """Enqueue a result.

        Puts the crawl result (`CrawlResult`) received as argument in the
        queue.
        """

    def get(self):
        """Returns the result at the top of the queue.

        Returns the crawl result (`CrawlResult`) at the top of the queue.  The
        result should be reported as processed using `report_done()`.  If there
        is not an available result an `EmptyQueueError` exception is raised.
        """
        raise EmptyQueueError()

    def report_done(self, result):
        """Reports a result as processed.
        """
