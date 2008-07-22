# -*- coding: utf-8 -*-

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

import aracne


setup(name='aracne',
      description='',
      url='',
      version=aracne.__version__,
      author=' '.join(aracne.__author__.split()[:-1]),
      author_email=aracne.__author__.split()[-1][1:-1],
      packages=['aracne', 'aracne.handlers', 'aracne.processors',
                'aracne.utils'],
      scripts=['scripts/aracne'],
)
