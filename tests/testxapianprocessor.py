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
import shutil
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.processor import XapianProcessor
from arachne.util.url import URL


class TestXapianProcessor(unittest.TestCase):

    def setUp(self):
        self._index_dir = os.path.join(TESTDIR, 'testxapianprocessor')
        self._sites_info = {
            'a78e6853355ad5cdc751ad678d15339382f9ed21':
                {'url': URL('ftp://atlantis.uh.cu/')},
            '7e019d6f671d336a0cc31f137ba034efb13fc327':
                {'url': URL('ftp://andromeda.uh.cu/')},
        }
        self._processor = XapianProcessor(self._sites_info, self._index_dir,
                                          None, None)

    def test_get_basename_terms(self):
        test_data = (
            (u'Arachne',
             [u'arachne']),

            (u'Yasser González Fernández',
             [u'yasser', u'gonzález', u'gonzalez', u'fernández', u'fernandez']),

            (u'Python-3.0rc1.tar.bz2',
             [u'python', u'3.0rc1', u'tar', u'bz2']),

            (u'07. (Let me be your) Teddy bear.mp3',
             [u'07', u'let', u'me', u'be', u'your', u'teddy', u'bear', u'mp3']),

            (u'dive_into_python.zip',
             [u'dive', u'into', u'python', u'zip']),

            (u'AFewCamelCasedWords',
             [u'few', u'camel', u'cased', u'words']),

            # The ' between letters should not split the string.
            (u'A hard day\'s night',
             [u'hard', u'day\'s', u'night']),

            (u'It should ignore this: ! # &.',
             [u'it', u'should', u'ignore', u'this']),

            # Do not return repeated terms.
            (u'Please, please me',
             [u'please', u'me']),
        )
        for basename, right_terms in test_data:
            terms = self._processor._get_basename_terms(basename)
            for term in terms:
                self.assertTrue(term in right_terms)
                right_terms.remove(term)
            self.assertEquals(len(right_terms), 0)

    def test_get_dirname_terms(self):
        # Don't test so hard since it only calls _get_basename_terms() for each
        # directory in the path.
        test_data = (
            (u'/Books/Programming/Python/dive_into_python.zip',
             [u'books', u'programming', u'python', u'dive', u'into', u'python']),

            # Do not return repeated terms.
            (u'/Music/The Beatles/Meet The Beatles!',
             [u'music', u'the', u'beatles', u'meet']),
        )
        for dirname, right_terms in test_data:
            terms = self._processor._get_dirname_terms(dirname)
            for term in terms:
                self.assertTrue(term in right_terms)
                right_terms.remove(term)
            self.assertEquals(len(right_terms), 0)

    def tearDown(self):
        if os.path.isdir(self._index_dir):
            self._processor.close()
            shutil.rmtree(self._index_dir)


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
