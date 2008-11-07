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

from arachne.processor import IndexProcessor
from arachne.result import CrawlResult
from arachne.task import CrawlTask
from arachne.url import URL


class TestIndexProcessor(unittest.TestCase):

    def setUp(self):
        self._index_dir = os.path.join(TESTDIR, 'testindexprocessor')
        self._sites_info = {
            'a78e6853355ad5cdc751ad678d15339382f9ed21':
                {'url': URL('ftp://atlantis.uh.cu/')},
            '7e019d6f671d336a0cc31f137ba034efb13fc327':
                {'url': URL('ftp://andromeda.uh.cu/')},
        }
        self._processor = IndexProcessor(self._sites_info, self._index_dir,
                                         None, None)

    def test_get_terms(self):
        test_data = (
            (u'Arachne',
             [u'arachne']),

            (u'arachne1.0',
             [u'arachne', u'1.0']),

            (u'Yasser González Fernández',
             [u'yasser', u'gonzález', u'gonzalez', u'fernández', u'fernandez']),

            (u'Python-3.0rc1.tar.bz2',
             [u'python', u'3.0', u'rc', u'1', u'tar', u'bz', u'2']),

            (u'07. (Let me be your) Teddy bear.mp3',
             [u'07', u'let', u'me', u'be', u'your', u'teddy', u'bear', u'mp', u'3']),

            (u'dive_into_python.zip',
             [u'dive', u'into', u'python', u'zip']),

            (u'AFewCamelCasedWords',
             [u'afewcamelcasedwords', u'few', u'camel', u'cased', u'words']),

            (u'It should ignore this: ! # &.',
             [u'it', u'should', u'ignore', u'this']),

            (u'Please, please me',
             [u'please', u'me']),

            (u'/Books/Programming/Python/dive_into_python',
             [u'books', u'programming', u'python', u'dive', u'into']),

            (u'/Music/The Beatles/Meet The Beatles!',
             [u'music', u'the', u'beatles', u'meet']),

            (u'The C Programming Language',
             [u'the', u'c', u'programming', u'language']),
        )
        for basename, right_terms in test_data:
            terms = self._processor._get_terms(basename)
            for term in terms:
                self.assertTrue(term in right_terms, term)
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
