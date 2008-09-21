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

    def __init__(self, url):
        """Initialize the URL from the string `url`.
        """
        result = urlparse.urlsplit(url.rstrip('/'))
        self._protocol = result.scheme
        self._username = result.username
        self._password = result.password
        self._host = result.netloc
        self._port = result.port
        self._url = result.geturl()
        if result.path:
            self._path = result.path
        else:
            # Include the / in the URL of the root directory.
            self._url = '%s/' % self._url
            self._path = '/'

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
        return URL('%s/%s' % (self._url.rstrip('/'), path.lstrip('/')))

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

    def _get_protocol(self):
        """Get method for the `protocol` property.
        """
        return self._protocol

    def _get_username(self):
        """Get method for the `username` property.
        """
        return self._username

    def _get_password(self):
        """Get method for the `password` property.
        """
        return self._password

    def _get_host(self):
        """Get method for the `host` property.
        """
        return self._host

    def _get_port(self):
        """Get method for the `port` property.
        """
        return self._port

    def _get_path(self):
        """Get method for the `path` property.
        """
        return self._path

    protocol = property(_get_protocol)

    username = property(_get_username)

    password = property(_get_password)

    host = property(_get_host)

    port = property(_get_port)

    path = property(_get_path)
