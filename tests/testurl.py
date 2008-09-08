#!/usr/bin/env python
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

import os
import sys
import pickle
import urlparse
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.util.url import URL


class TestURL(unittest.TestCase):

    def setUp(self):
        self._urls = (
            'ftp://deltha.uh.cu:21/debian/',
            'http://deltha.uh.cu:80/~yglez/',
            'smb://software.matcom.uh.cu/',
        )

    def test_init(self):
        for url in self._urls:
            self._check(URL(url), url)

    def test_pickling(self):
        for url in self._urls:
            data = pickle.dumps(URL(url))
            self._check(pickle.loads(data), url)

    def _check(self, urlobj, url):
        result = urlparse.urlsplit(url)
        self.assertEquals(urlobj.protocol, result.scheme)
        self.assertEquals(urlobj.user, result.username)
        self.assertEquals(urlobj.passwd, result.password)
        self.assertEquals(urlobj.host, result.netloc)
        self.assertEquals(urlobj.port, result.port)
        self.assertEquals(urlobj.path, result.path)
        self.assertEquals(str(urlobj), result.geturl())


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', dest='verbosity', default='2',
                      type='choice', choices=['0', '1', '2'],
                      help='verbosity level: 0 = minimal, 1 = normal, 2 = all')
    options, args = parser.parse_args()
    module = os.path.basename(__file__)[:-3]
    suite = unittest.TestLoader().loadTestsFromName(module)
    runner = unittest.TextTestRunner(verbosity=int(options.verbosity))
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
