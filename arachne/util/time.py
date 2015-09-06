# -*- coding: utf-8 -*-
#
# Arachne: Search engine for files shared via FTP and similar protocols.
# Copyright (C) 2008-2010 Yasser González Fernández <ygonzalezfernandez@gmail.com>
# Copyright (C) 2008-2010 Ariel Hernández Amador <gnuaha7@gmail.com>
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

# Based on the ones from the Time module of rdiff-backup
# (http://rdiff-backup.nongnu.org/).

"""Functions used to parse and print time deltas.
"""

import re


# Number of seconds for each time suffix.
_SUFFIXES = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24,
}

_SUFFIXES_RE = re.compile(r'^([0-9]+)([smhd])')


def secs_to_readable(secs):
    """Convert a number of seconds to a readable string.

    The output string will be like: 1 day, 2 hours, 20 minutes and 15 seconds.
    """
    parts = []
    days, secs = divmod(secs, _SUFFIXES['d'])
    if days > 1:
        parts.append('%d days' % days)
    elif days == 1:
        parts.append('1 day')
    hours, secs = divmod(secs, _SUFFIXES['h'])
    if hours > 1:
        parts.append('%d hours' % hours)
    elif hours == 1:
        parts.append('1 hour')
    mins, secs = divmod(secs, _SUFFIXES['m'])
    if mins > 1:
        parts.append('%d minutes' % mins)
    elif mins == 1:
        parts.append('1 minute')
    if secs > 1:
        parts.append('%d seconds' % secs)
    elif secs == 1:
        parts.append('1 second')
    # Build the final string from the parts.
    i = len(parts)
    if i == 1:
        return parts[0]
    elif i == 2:
        return ' and '.join(parts)
    else:
        return '%s and %s' % (', '.join(parts[:i - 1]), parts[i - 1])


def str_to_secs(intstr):
    """Convert a string expressing an interval to seconds.

    The input string should be like: 1d2h20m15s. If the string does not
    contains any suffix is assumed that it is a number of seconds. If the given
    string contains spaces they will be striped before expanding the time
    suffixes. If the string is invalid `None` is returned.
    """
    intstr = intstr.replace(' ', '')
    try:
        secs = int(intstr)
    except ValueError:
        # The interval string is not a number of seconds.
        pass
    else:
        if secs >= 0:
            return secs
        else:
            return None
    # Parse suffixes.
    secs = 0
    while intstr:
        match = _SUFFIXES_RE.match(intstr)
        if match:
            value, suffix = int(match.group(1)), match.group(2)
            if suffix not in _SUFFIXES or value < 0:
                # Invalid interval string.
                return None
            else:
                secs += value * _SUFFIXES[suffix]
                intstr = intstr[match.end(0):]
        else:
            # Invalid interval string.
            return None
    return secs
