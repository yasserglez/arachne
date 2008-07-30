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


class ResultProcessor(object):
    """Crawl result processor.

    Abstract base class that should be subclassed by all the available
    processors.  Provides a way for extending the crawler to support other ways
    of processing the crawl results (`CrawlResult`).  A instance of a subclass
    of this class is managed by the `ProcessorManager`.
    """

    def __init__(self, task_queue, result_queue):
        """Initialize instances.

        The `ProcessorManager` will create an instace of a subclass providing
        an instance of `TaskQueue` and `ResultQueue` as arguments.  This
        implementation just set the `task_queue` and `result_queue` arguments
        as `_task_queue` and `_result_queue` attributes.
        """
        self._task_queue = task_queue
        self._result_queue = result_queue

    def process(self, result):
        """Process the crawl result.

        This is just an abstract method, it does nothing.  You should override
        this method in a subclass to implement a result processor.
        """
