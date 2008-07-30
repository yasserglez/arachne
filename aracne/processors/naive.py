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

from aracne.processors import ResultProcessor


class NaiveProcessor(ResultProcessor):
    """Naive result processor.

    This is a naive result processor.  It takes each one of the subdirectories
    of the crawl result (`CrawlResult`), creates a new crawl task (`CrawTask`)
    and inserts it with the current timestamp as priority.
    """

    def __init__(self, task_queue, result_queue):
        """Initialize attributes.
        """
        super(NaiveProcessor, self).__init__(task_queue, result_queue)

    def process(self, result):
        """Process crawl result.

        Takes each one of the subdirectories of the crawl result
        (`CrawlResult`), creates a new crawl task (`CrawTask`) and inserts it
        with the current timestamp as priority.
        """
