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

"""Protocol handlers.
"""

import os

from aracne.index.result import CrawlResult


class ProtocolHandler(object):
    """Protocol handler.

    Abstract class that should be subclassed by all supported protocols in the
    crawler.  This provides a way to extend the crawler to support new
    protocols.  Instances of this class are used by the `SiteCrawler`.

    The subclasses should set the `scheme` class attribute to the URL scheme
    specifier for the protocol.
    """

    scheme = ''

    def __init__(self, sites_info):
        """Initialize the protocol handler.

        The `sites_info` argument will be a dictionary mapping site IDs to the
        information for the sites.  This can be usefull to support advanced
        settings for a site (e.g. proxy server).
        """
        raise NotImplementedError()

    def execute(self, task):
        """Execute the task and return the result.

        If the task is successfully executed the `CrawlResult` instance should
        be returned, `None` otherwise.
        """
        raise NotImplementedError()


class FileHandler(ProtocolHandler):
    """Handler local files.
    """

    scheme = 'file'

    def __init__(self, sites_info):
        """Initialize handler.
        """

    def execute(self, task):
        """Execute the task and return the result.
        """
        try:
            dir_path = task.url.path
            if os.path.isdir(dir_path):
                result = CrawlResult(task)
                for entry in os.listdir(dir_path):
                    data = {}
                    entry_path = os.path.join(dir_path, entry)
                    data['isdir'] = os.path.isdir(entry_path)
                    if not data['isdir']:
                        data['size'] = os.path.getsize(entry_path)
                    result.append(entry, data)
            else:
                result = CrawlResult(task, False)
        except OSError:
            return None
        else:
            return result
