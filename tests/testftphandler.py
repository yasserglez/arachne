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
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.handler import FTPHandler


class TestFTPHandler(unittest.TestCase):

    def setUp(self):
        self._list_responses = (
            # UNIX-style listing.
            ('drwxr-xr-x   12 1000     1000         4096 Jun 18 20:57 The Beatles',
             ('The Beatles', True)),
            ('drwxr-xr-x    2 0        0            4096 Nov 07  2007 Help!',
             ('Help!', True)),
            ('-rw-r--r--    1 1000     1000          110 Jul 04 16:44 front.png',
             ('front.png', False)),
            ('-r--r--r--    1 0        0         1978805 Aug 23  2007 13. Yesterday.mp3',
             ('13. Yesterday.mp3', False)),
            ('lrwxrwxrwx    1 0        0            7 Jan 25 00:17 bin -> usr/bin',
             ('bin', None)),
            # Microsoft's FTP servers for Windows.
            ('----------   1 owner    group         1803128 Jul 10 10:18 front.png',
             ('front.png', False)),
            ('d---------   1 owner    group               0 May  9 19:45 The Beatles',
             ('The Beatles', True)),
            # MSDOS format.
            ('01-29-08  09:16AM       <DIR>          The Beatles',
             ('The Beatles', True)),
            ('01-29-08  09:17AM       <DIR>          Help!',
             ('Help!', True)),
            ('12-14-07  06:44PM              2161652 front.png',
             ('front.png', False)),
            ('01-16-08  05:47PM               429384 13. Yesterday.mp3',
             ('13. Yesterday.mp3', False)),
            # Easily Parsed LIST Format.
            ('+i8388621.29609,m824255902,/,\tThe Beatles',
             ('The Beatles', True)),
            ('+i8388621.48594,m825718503,r,s280,\t13. Yesterday.mp3',
             ('13. Yesterday.mp3', False)),
            # Lines that should be ignored (aditional information).
            ('total 14786', None),
            ('Total of 11 Files, 10966 Blocks', None),
        )
        self._sites_info = []
        self._handler = FTPHandler(self._sites_info)

    def test_parse_list(self):
        for line, parsed in self._list_responses:
            self.assertEquals(self._handler._parse_list(line), parsed)


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
