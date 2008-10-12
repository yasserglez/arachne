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
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.util.url import URL


class TestURL(unittest.TestCase):

    def setUp(self):
        self._urls = (
            ('file:///',
             ('file', None, None, None, None, '/', '/'),
             ('etc', 'file:///etc')),

            ('file:///home',
             ('file', None, None, None, None, '/home', 'home'),
             ('yglez', 'file:///home/yglez')),

            ('ftp://deltha.uh.cu/',
             ('ftp', None, None, 'deltha.uh.cu', None, '/', '/'),
             ('debian', 'ftp://deltha.uh.cu/debian')),

            ('ftp://username:password@deltha.uh.cu/',
             ('ftp', 'username', 'password', 'deltha.uh.cu', None, '/', '/'),
             ('debian', 'ftp://username:password@deltha.uh.cu/debian')),

            ('ftp://deltha.uh.cu:21/',
             ('ftp', None, None, 'deltha.uh.cu', 21, '/', '/'),
             ('debian', 'ftp://deltha.uh.cu:21/debian')),

            ('ftp://username:password@deltha.uh.cu:21/',
             ('ftp', 'username', 'password', 'deltha.uh.cu', 21, '/', '/'),
             ('debian', 'ftp://username:password@deltha.uh.cu:21/debian')),

            ('ftp://deltha.uh.cu/debian',
             ('ftp', None, None, 'deltha.uh.cu', None, '/debian', 'debian'),
             ('pool', 'ftp://deltha.uh.cu/debian/pool')),
        )

    def test_properties(self):
        for url_str, attrs, join_info in self._urls:
            url = URL(url_str)
            self.assertEquals(url.scheme, attrs[0])
            self.assertEquals(url.username, attrs[1])
            self.assertEquals(url.password, attrs[2])
            self.assertEquals(url.hostname, attrs[3])
            self.assertEquals(url.port, attrs[4])
            self.assertEquals(url.path, attrs[5])
            self.assertEquals(url.basename, attrs[6])

    def test_join(self):
        for url_str, attrs, join_info in self._urls:
            url = URL(url_str)
            self.assertEquals(str(url.join(join_info[0])), join_info[1])

    def test_pickling(self):
        for url_str, attrs, join_info in self._urls:
            url = pickle.loads(pickle.dumps(URL(url_str)))
            self.assertEquals(url.scheme, attrs[0])
            self.assertEquals(url.username, attrs[1])
            self.assertEquals(url.password, attrs[2])
            self.assertEquals(url.hostname, attrs[3])
            self.assertEquals(url.port, attrs[4])
            self.assertEquals(url.path, attrs[5])
            self.assertEquals(url.basename, attrs[6])


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', dest='verbosity', default='2',
                      type='choice', choices=['0', '1', '2'],
                      help='verbosity level: 0 = minimal, 1 = normal, 2 = all')
    options = parser.parse_args()[0]
    module = os.path.basename(__file__)[:-3]
    suite = unittest.TestLoader().loadTestsFromName(module)
    runner = unittest.TextTestRunner(verbosity=int(options.verbosity))
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
