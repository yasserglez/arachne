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


class CrawlTask(object):
    """Crawl task.

    Represents the action of retrieving the list of files and directories found
    inside of a given directory in a site.  The result of executing this task
    is a `CrawlResult`.
    """


class TaskQueue(object):
    """Task queue.

    Collects and organizes the pending `CrawlTask`.
    """
