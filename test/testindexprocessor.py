# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009 Yasser González Fernández <yglez@uh.cu>
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
import shutil
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.processor import IndexProcessor


class TestIndexProcessor(unittest.TestCase):

    def test_get_terms(self):
        test_data = (
            (u'Arachne',
             [u'arachne']),

            (u'arachne1.0',
             [u'arachne', u'1.0']),

            (u'Yasser González Fernández',
             [u'yasser', u'gonzález', u'gonzalez', u'fernández', u'fernandez']),

            (u'Python-3.0rc1.tar.bz2',
             [u'python', u'3.0', u'1', u'tar', u'2']),

            (u'07. (Let me be your) Teddy bear.mp3',
             [u'let', u'your', u'teddy', u'bear', u'3']),

            (u'dive_into_python.zip',
             [u'dive', u'into', u'python', u'zip']),

            (u'AFewCamelCasedWords',
             [u'afewcamelcasedwords', u'few', u'camel', u'cased', u'words']),

            (u'It should ignore this: ! # &.',
             [u'should', u'ignore', u'this']),

            (u'Please, please me',
             [u'please']),

            (u'/Books/Programming/Python/dive_into_python',
             [u'books', u'programming', u'python', u'dive', u'into']),

            (u'/Music/The Beatles/Meet The Beatles!',
             [u'music', u'the', u'beatles', u'meet']),

            (u'The C Programming Language',
             [u'the', u'c', u'programming', u'language']),
        )
        for basename, right_terms in test_data:
            terms = IndexProcessor.get_terms(basename)
            for term in terms:
                self.assertTrue(term in right_terms, term)
                right_terms.remove(term)
            self.assertEquals(len(right_terms), 0)


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
