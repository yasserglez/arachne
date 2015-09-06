#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

from arachne import __version__


setup(name='Arachne',
      version=__version__,
      license='GNU General Public License version 3 or any later version.',
      description='Search engine for files shared via FTP and similar protocols.',
      platforms=['POSIX'],
      packages=['arachne', 'arachne.util'],
      package_dir={'arachne': 'arachne'},
      data_files=[
        ('/etc/init.d/', ['data/arachned']),
        ('/etc/arachne/', ['data/daemon.conf', 'data/sites.conf']),
        ('/usr/share/doc/arachne/', ['LICENSE.txt', 'README.md', 'THANKS.md']),
        # The arachned script should be copied to the /usr/sbin/ directory.
        ('/usr/sbin/', ['scripts/arachned']),
        # Empty directories required by the default configuration.
        ('/var/run/arachne/', []),
        ('/var/spool/arachne', []),
        ('/var/lib/arachne/', []),
        ('/var/log/arachne/', []),
      ],
)
