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

from distutils.core import setup

from aracne import __author__, __version__


setup(name='Aracne',
      version=__version__,
      license='GNU General Public License version 3 or later',
      description='Networked file search engine.',
      long_description='',
      url='',
      download_url='',
      author=' '.join(__author__.split()[:-1]),
      author_email=__author__.split()[-1].strip('<>'),
      platforms=[],
      packages=['aracne', 'aracne.indexer', 'aracne.searcher', 'aracne.utils'],
      package_dir={'aracne': 'aracne'},
      data_files=[
        ('/etc/init.d/', ['data/aracne']),
        ('/etc/aracne/', ['data/indexer.conf', 'data/searcher.conf',
                          'data/sites.conf']),
        ('share/doc/aracne/', ['AUTHORS', 'INSTALL', 'LICENSE', 'README',
                               'THANKS']),
        # Daemon scripts are installed as data files because they should be
        # copied to the /usr/sbin/ directory.
        ('/usr/sbin/', ['scripts/aracne-indexer', 'scripts/aracne-searcher']),
        # Empty directories required by the default configuration.
        ('/var/run/aracne/', []),
        ('/var/lib/spool/aracne', []),
        ('/var/lib/aracne/', []),
        ('/var/log/aracne/', []),
      ],
)
