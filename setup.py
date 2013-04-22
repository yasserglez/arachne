#!/usr/bin/env python
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

from distutils.core import setup

from arachne import __version__


setup(name='Arachne',
      version=__version__,
      license='GNU General Public License version 3 or any later version.',
      description='Search engine for files and directories.',
      long_description='Arachne is a search engine for files and directories' \
          + ' shared via FTP and similar\nprotocols in a networked environment.',
      platforms=['POSIX'],
      packages=['arachne', 'arachne.util'],
      package_dir={'arachne': 'arachne'},
      data_files=[
        ('/etc/init.d/', ['data/arachned']),
        ('/etc/arachne/', ['data/daemon.conf', 'data/sites.conf']),
        ('/usr/share/doc/arachne/', ['AUTHORS.txt', 'INSTALL.txt',
                                     'LICENSE.txt', 'README.txt',
                                     'THANKS.txt']),
        # The arachned script should be copied to the /usr/sbin/ directory.
        ('/usr/sbin/', ['scripts/arachned']),
        # Empty directories required by the default configuration.
        ('/var/run/arachne/', []),
        ('/var/spool/arachne', []),
        ('/var/lib/arachne/', []),
        ('/var/log/arachne/', []),
      ],
)
