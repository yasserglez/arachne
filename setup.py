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

from arachne import __author__, __version__


setup(name='Arachne',
      version=__version__,
      license='GNU General Public License version 3 or any later version',
      description='File search engine.',
      long_description='',
      url='',
      download_url='',
      author=' '.join(__author__.split()[:-1]),
      author_email=__author__.split()[-1].strip('<>'),
      platforms=[],
      packages=['arachne', 'arachne.indexer', 'arachne.searcher',
                'arachne.util'],
      package_dir={'arachne': 'arachne'},
      data_files=[
        ('/etc/init.d/', ['data/arachne']),
        ('/etc/arachne/', ['data/indexer.conf', 'data/searcher.conf',
                          'data/sites.conf']),
        ('share/doc/arachne/', ['AUTHORS', 'INSTALL', 'LICENSE', 'README',
                               'THANKS']),
        # Daemon scripts are installed as data files because they should be
        # copied to the /usr/sbin/ directory.
        ('/usr/sbin/', ['scripts/arachne-indexer', 'scripts/arachne-searcher']),
        # Empty directories required by the default configuration.
        ('/var/run/arachne/', []),
        ('/var/lib/spool/arachne', []),
        ('/var/lib/arachne/', []),
        ('/var/log/arachne/', []),
      ],
)
