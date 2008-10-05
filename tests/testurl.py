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

from arachne.utils.url import URL


class TestURL(unittest.TestCase):

    def setUp(self):
        self._url = 'http://deltha.uh.cu:21/debian'
        self._basename = 'debian'
        self._join_path = 'pool'
        self._joined_url = 'http://deltha.uh.cu:21/debian/pool'
        self._urlobj = URL(self._url)

    def test_properties(self):
        result = urlparse.urlsplit(self._url)
        self.assertEquals(self._urlobj.scheme, result.scheme)
        self.assertEquals(self._urlobj.username, result.username)
        self.assertEquals(self._urlobj.password, result.password)
        self.assertEquals(self._urlobj.host, result.netloc)
        self.assertEquals(self._urlobj.port, result.port)
        self.assertEquals(self._urlobj.path, result.path)

    def test_basename(self):
        self.assertEquals(self._urlobj.basename(), self._basename)

    def test_join(self):
        joined_urlobj = self._urlobj.join(self._join_path)
        self.assertEquals(str(joined_urlobj), self._joined_url)

    def test_pickling(self):
        urlobj = pickle.loads(pickle.dumps(self._urlobj))
        self.assertEquals(self._urlobj.scheme, urlobj.scheme)
        self.assertEquals(self._urlobj.username, urlobj.username)
        self.assertEquals(self._urlobj.password, urlobj.password)
        self.assertEquals(self._urlobj.host, urlobj.host)
        self.assertEquals(self._urlobj.port, urlobj.port)
        self.assertEquals(self._urlobj.path, urlobj.path)


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
