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

"""Custom filters for the Arachne application.
"""

import re

from django import template
from django.utils.html import escape
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe


register = template.Library()


_URLIZEPARTS_RE = re.compile(r'^(?P<root>[a-zA-Z0-9+-.]+://[^/]*)(?P<dirname>/|/.*/)(?P<basename>[^/]+)$')


@register.filter
@stringfilter
def urlize_dirname(url, title='Go to directory'):
    """Create an HTML link for each path component of the dirname of the URL.
    """
    LINK = '<a href="%%s" title="%s">%%s</a>' % title
    try:
        parts = []
        match = _URLIZEPARTS_RE.match(url)
        cur_url = match.group('root')
        parts.append(LINK % (escape(cur_url), escape(cur_url)))
        for part in filter(None, match.group('dirname').split('/')):
            cur_url += '/' + part
            parts.append(LINK % (escape(cur_url), escape(part)))
        resp = '/'.join(parts)
    except Exception:
        resp = LINK % (escape(url), escape(url))
    return mark_safe(resp)


@register.filter
@stringfilter
def urlize_basename(url, title='Go to directory'):
    """Create an HTML link for the basename of the URL.
    """
    LINK = '<a href="%%s" title="%s">%%s</a>' % title
    try:
        match = _URLIZEPARTS_RE.match(url)
        resp = LINK % (escape(url), escape(match.group('basename')))
    except Exception:
        resp = LINK % (escape(url), escape(url))
    return mark_safe(resp)
