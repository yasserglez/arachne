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

from optparse import OptionParser

import locate


USAGE = '%prog [options]'

VERSION = '%%prog %s\n%s.\nThis is free software: you are free to change ' \
    'and redistribute it under the\nterms of the GNU GPL version 3 or later ' \
    '<http://www.gnu.org/licenses/gpl.html>.\nThere is NO WARRANTY, to the' \
    'extent permitted by law.' % (locate.__version__, locate.__copyright__)

DEFAULT_CONF = '/etc/locate.conf'


def main():
    option_parser = OptionParser(usage=USAGE, version=VERSION)
    option_parser.add_option('-c', '--conf', metavar='FILE', default=DEFAULT_CONF,
                             help='specify configuration file (default %default)')
    (options, args) = option_parser.parse_args()
