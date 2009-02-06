# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009 Yasser González Fernández <yglez@uh.cu>
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

"""Django views for the Arachne website.
"""

from django.shortcuts import render_to_response

from arachne.searcher import IndexSearcher

from arachnesite import settings


def basic(request):
    """Show the basic search form.
    """
    context = {
        'media_url': settings.MEDIA_URL,
        'search_type': 'basic',
    }
    return render_to_response('search.html', context)


def advanced(request):
    """Show the advanced search form.
    """
    searcher = IndexSearcher(settings.DATABASE_DIR)
    context = {
        'media_url': settings.MEDIA_URL,
        'search_type': 'advanced',
        'sites': searcher.get_sites(),
    }
    return render_to_response('search.html', context)


def search(request):
    """Execute the query and show results.
    """
    context = {
        'media_url': settings.MEDIA_URL,
        'results': results,
    }
    return render_to_response('results.html', context)
