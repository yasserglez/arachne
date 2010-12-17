# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009, 2010 Yasser González Fernández <ygonzalezfernandez@gmail.com>
# Copyright (C) 2008, 2009, 2010 Ariel Hernández Amador <gnuaha7@gmail.com>
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

from arachne.util.time import secs_to_readable, str_to_secs


class TestTimeUtils(unittest.TestCase):

    def test_secs_to_readable(self):
        values = {
            1: '1 second',
            60: '1 minute',
            60 * 60: '1 hour',
            60 * 60 * 24: '1 day',
            2: '2 seconds',
            60 * 2: '2 minutes',
            60 * 60 * 2: '2 hours',
            60 * 60 * 24 * 2: '2 days',
            60 + 1: '1 minute and 1 second',
            60 * 60 + 60 + 1: '1 hour, 1 minute and 1 second',
            60 * 60 * 24 + 60 * 60 + 60 + 1:
                '1 day, 1 hour, 1 minute and 1 second',
        }
        for secs, readable in values.iteritems():
            self.assertEquals(secs_to_readable(secs), readable)

    def test_str_to_secs(self):
        values = {
            # Valid string.
            '1': 1,
            '1s': 1,
            '1m': 60,
            '1h': 60 * 60,
            '1d': 60 * 60 * 24,
            '2': 2,
            '2s': 2,
            '2m': 60 * 2,
            '2h': 60 * 60 * 2,
            '2d': 60 * 60 * 24 * 2,
            '1m1s': 60 + 1,
            '1h1m1s': 60 * 60 + 60 + 1,
            '1d1h1m1s': 60 * 60 * 24 + 60 * 60 + 60 + 1,
            # Invalid strings.
            'Invalid string': None,
            '-1': None,
            '-1s': None,
        }
        for suffixed, secs in values.iteritems():
            self.assertEquals(str_to_secs(suffixed), secs)


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
