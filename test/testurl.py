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
import pickle
import optparse
import unittest

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from arachne.url import URL


class TestURL(unittest.TestCase):

    def setUp(self):
        self._encoding = 'utf-8'
        self._urls = (
            ('file:///', True,
             (u'file', None, None, None, None, u'/', u'/', u'/'),
             ('etc', 'file:///etc')),

            ('file:///home', False,
             (u'file', None, None, None, None, u'/home', u'/', u'home'),
             ('yglez', 'file:///home/yglez')),

            ('file:///home/yglez', False,
             (u'file', None, None, None, None, u'/home/yglez', u'/home', u'yglez'),
             ('projects', 'file:///home/yglez/projects')),

            ('ftp://deltha.uh.cu/', True,
             (u'ftp', None, None, u'deltha.uh.cu', None, u'/', u'/', u'/'),
             ('debian', 'ftp://deltha.uh.cu/debian')),

            ('ftp://user:passwd@deltha.uh.cu/', True,
             (u'ftp', u'user', u'passwd', u'deltha.uh.cu', None, u'/', u'/', u'/'),
             ('debian', 'ftp://user:passwd@deltha.uh.cu/debian')),

            ('ftp://deltha.uh.cu:21/', True,
             (u'ftp', None, None, u'deltha.uh.cu', 21, u'/', u'/', u'/'),
             ('debian', 'ftp://deltha.uh.cu:21/debian')),

            ('ftp://user:passwd@deltha.uh.cu:21/', True,
             (u'ftp', u'user', u'passwd', u'deltha.uh.cu', 21, u'/', u'/', u'/'),
             ('debian', 'ftp://user:passwd@deltha.uh.cu:21/debian')),

            ('file:///unívoco/güije', False,
             (u'file', None, None, None, None, u'/unívoco/güije', u'/unívoco', u'güije'),
             ('gruñón', 'file:///unívoco/güije/gruñón')),
        )

    def test_properties(self):
        for url_str, is_root, attrs, join_info in self._urls:
            url = URL(url_str, is_root)
            self.assertEquals(url.is_root, is_root)
            self.assertEquals(url.scheme, attrs[0])
            self.assertEquals(url.username, attrs[1])
            self.assertEquals(url.password, attrs[2])
            self.assertEquals(url.hostname, attrs[3])
            self.assertEquals(url.port, attrs[4])
            self.assertEquals(url.path, attrs[5])
            self.assertEquals(url.dirname, attrs[6])
            self.assertEquals(url.basename, attrs[7])

    def test_properties_unicode_args(self):
        for url_str, is_root, attrs, join_info in self._urls:
            url = URL(url_str.decode(self._encoding), is_root)
            self.assertEquals(url.is_root, is_root)
            self.assertEquals(url.scheme, attrs[0])
            self.assertEquals(url.username, attrs[1])
            self.assertEquals(url.password, attrs[2])
            self.assertEquals(url.hostname, attrs[3])
            self.assertEquals(url.port, attrs[4])
            self.assertEquals(url.path, attrs[5])
            self.assertEquals(url.dirname, attrs[6])
            self.assertEquals(url.basename, attrs[7])

    def test_join(self):
        for url_str, is_root, attrs, join_info in self._urls:
            url = URL(url_str, is_root)
            joined_url = url.join(join_info[0])
            self.assertEquals(joined_url.is_root, False)
            # Joined URLs should not be root.
            self.assertEquals(str(joined_url), join_info[1])

    def test_join_unicode_args(self):
        for url_str, is_root, attrs, join_info in self._urls:
            url = URL(url_str.decode(self._encoding), is_root)
            joined_url = url.join(join_info[0].decode(self._encoding))
            # Joined URLs should not be root.
            self.assertEquals(joined_url.is_root, False)
            self.assertEquals(str(joined_url), join_info[1])

    def test_pickling(self):
        for url_str, is_root, attrs, join_info in self._urls:
            url = pickle.loads(pickle.dumps(URL(url_str, is_root)))
            self.assertEquals(url.is_root, is_root)
            self.assertEquals(url.scheme, attrs[0])
            self.assertEquals(url.username, attrs[1])
            self.assertEquals(url.password, attrs[2])
            self.assertEquals(url.hostname, attrs[3])
            self.assertEquals(url.port, attrs[4])
            self.assertEquals(url.path, attrs[5])
            self.assertEquals(url.dirname, attrs[6])
            self.assertEquals(url.basename, attrs[7])

    def test_type_unicode(self):
       for url_str, is_root, attrs, join_info in self._urls:
           url = URL(url_str, is_root)
           self.assertTrue(type(url.scheme) is unicode)
           if attrs[1] is not None:
               self.assertTrue(type(url.username) is unicode)
           if attrs[2] is not None:
               self.assertTrue(type(url.password) is unicode)
           if attrs[3] is not None:
               self.assertTrue(type(url.hostname) is unicode)
           self.assertTrue(type(url.path) is unicode)
           self.assertTrue(type(url.dirname) is unicode)
           self.assertTrue(type(url.basename) is unicode)
           pickled_url = pickle.loads(pickle.dumps(url))
           self.assertTrue(type(pickled_url.scheme) is unicode)
           if attrs[1] is not None:
               self.assertTrue(type(pickled_url.username) is unicode)
           if attrs[2] is not None:
               self.assertTrue(type(pickled_url.password) is unicode)
           if attrs[3] is not None:
               self.assertTrue(type(pickled_url.hostname) is unicode)
           self.assertTrue(type(pickled_url.path) is unicode)
           self.assertTrue(type(pickled_url.dirname) is unicode)
           self.assertTrue(type(pickled_url.basename) is unicode)


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
