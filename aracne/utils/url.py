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

"""URL class.
"""

import urlparse


class URL(object):
    """Uniform Resource Locator.
    """

    protocol = property(lambda self: self._protocol)

    username = property(lambda self: self._username)

    password = property(lambda self: self._password)

    host = property(lambda self: self._host)

    port = property(lambda self: self._port)

    path = property(lambda self: self._path)

    def __init__(self, url):
        """Initialize the URL from the string `url`.
        """
        result = urlparse.urlsplit(url.rstrip('/'))
        self._protocol = result.scheme
        self._username = result.username
        self._password = result.password
        self._host = result.netloc
        self._port = result.port
        self._path = result.path if result.path else '/'
        self._url = result.geturl()

    def __str__(self):
        """Return the URL as string.
        """
        return self._url

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'url': self._url,
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self.__init__(state['url'])

    def join(self, path):
        """Join a path to the URL and return the new URL.
        """
        return URL('%s/%s' %(self._url, path.lstrip('/')))

    def basename(self):
        """Return last path component as string.

        This method will return '/' for URL of the root directory.
        """
        # If the path ends with a / then it is the root directory and it is
        # returned.  Otherwise, the basename will be the rest of the string
        # after the last / found.
        if self._path.endswith('/'):
            return self._path
        else:
            i = self._path.rindex('/')
            return self._path[i + 1:]
