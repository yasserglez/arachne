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

import urlparse


class URL(object):
    """Uniform Resource Locator representation.
    """

    def __init__(self, url):
        """Initialize the URL from the string `url`.
        """
        result = urlparse.urlsplit(url)
        self.protocol = result.scheme
        self.user = result.username
        self.passwd = result.password
        self.host = result.netloc
        self.port = result.port
        self.path = result.path
        self.url = result.geturl()

    def __str__(self):
        """Return the URL as string.
        """
        return self.url

    def __getstate__(self):
        """Used by pickle when the class is serialized.
        """
        return self.url

    def __setstate__(self, url):
        """Used by pickle when the class is unserialized.
        """
        self.__init__(url)
