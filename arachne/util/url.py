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
        self._encoding = 'utf-8'
        if not isinstance(url, unicode):
            url = url.decode(self._encoding)
        splitted_url = urlparse.urlsplit(url)
        root_url = u'%s://%s/' % (splitted_url.scheme, splitted_url.netloc)
        self._scheme = splitted_url.scheme
        self._username = splitted_url.username
        self._password = splitted_url.password
        self._hostname = splitted_url.hostname
        self._port = splitted_url.port
        path = url[len(root_url):].rstrip(u'/')
        if not path:
            self._path = u'/'
            self._url = root_url
        else:
            self._path = u'/%s' % path.lstrip(u'/')
            self._url = u'%s%s' % (root_url, path.lstrip(u'/'))

    def __str__(self):
        """Return the URL as string.
        """
        return self._url.encode(self._encoding)

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'url': self._url.encode(self._encoding),
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self.__init__(state['url'])

    def join(self, path):
        """Join a path to the URL and return the new URL.
        """
        if not isinstance(path, unicode):
            path = path.decode(self._encoding)
        base_url = self._url[:-1] if self._path == u'/' else self._url
        return URL(u'%s/%s' % (base_url, path.lstrip(u'/')))

    def _get_scheme(self):
        """Get method for the `scheme` property.
        """
        return self._scheme

    def _get_username(self):
        """Get method for the `username` property.
        """
        return self._username

    def _get_password(self):
        """Get method for the `password` property.
        """
        return self._password

    def _get_hostname(self):
        """Get method for the `hostname` property.
        """
        return self._hostname

    def _get_port(self):
        """Get method for the `port` property.
        """
        return self._port

    def _get_path(self):
        """Get method for the `path` property.
        """
        return self._path

    def _get_basename(self):
        """Get method for the `basename` property.

        This method will return '/' for URL of the root directory.
        """
        if self._path == u'/':
            return self._path
        else:
            return self._path[self._path.rindex(u'/') + 1:]

    scheme = property(_get_scheme)

    username = property(_get_username)

    password = property(_get_password)

    hostname = property(_get_hostname)

    port = property(_get_port)

    path = property(_get_path)

    basename = property(_get_basename)
