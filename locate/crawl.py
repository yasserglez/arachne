# -*- coding: utf-8 -*-

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


class CrawlWorker(object):
    """Crawl worker.

    Executes each one of the `CrawlTasks` received from the `CrawlManager` and
    returns a `CrawlResult`.  Contacts the site and retrieves the list of files
    and directories found inside the given directory.
    """


class CrawlManager(object):
    """Crawl manager.

    Creates, manages and feeds a configurable number of `CrawlWorkers` with
    `CrawlTasks` received from the `TaskQueue` and reports the `CrawlResults`
    to the `ResultQueue`.
    """
