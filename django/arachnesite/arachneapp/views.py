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

"""Django views for the Arachne application.
"""

from django.conf import settings
from django.shortcuts import render_to_response

from arachne import __version__
from arachne.searcher import IndexSearcher


RESULTS_PER_PAGE = 20

DEFAULT_CONTEXT = {
    'version': __version__,
    'root': settings.ARACHNE_ROOT,
    'media_url': settings.ARACHNE_MEDIA_URL,
}


def basic(request):
    """Show the basic search form.
    """
    context = DEFAULT_CONTEXT.copy()
    context['search_type'] = 'basic'
    return render_to_response('search.html', context)


def advanced(request):
    """Show the advanced search form.
    """
    searcher = IndexSearcher(settings.ARACHNE_DATABASE_DIR)
    context = DEFAULT_CONTEXT.copy()
    context['search_type'] = 'advanced'
    context['sites'] = searcher.get_sites()
    return render_to_response('search.html', context)


def results(request):
    """Execute the query and show results.
    """
    context = DEFAULT_CONTEXT.copy()
    query = request.POST.get('query', '')
    context['query'] = query
    if query:
        search_type = request.POST.get('searchtype', 'basic')
        context['search_type'] = search_type
        offset = int(request.POST.get('offset', 0))
        # Ensure valid page links, at least, for the next 10 pages.
        check_at_least = offset + (11 * RESULTS_PER_PAGE)
        searcher = IndexSearcher(settings.ARACHNE_DATABASE_DIR)
        if search_type == 'advanced':
            # Advanced search.
            sites = []
            site_ids = []
            for site in searcher.get_sites():
                included = request.POST.get(site['id'], None) != None
                if included:
                    sites.append(site)
                    site_ids.append(site['id'])
            context['sites'] = sites
            filetype = request.POST.get('filetype', 'both')
            context['filetype'] = filetype
            if filetype == 'file':
                filetype = IndexSearcher.SEARCH_FILE
            elif filetype == 'dir':
                filetype = IndexSearcher.SEARCH_DIRECTORY
            else:
                filetype = IndexSearcher.SEARCH_ALL
            estimated_results, results = \
                searcher.search(query, offset, RESULTS_PER_PAGE,
                                check_at_least, site_ids, filetype)
        else:
            # Basic search.
            estimated_results, results = \
                searcher.search(query, offset, RESULTS_PER_PAGE,
                                check_at_least)
        context['has_results'] = len(results) != 0
        if context['has_results']:
            for num, result in enumerate(results):
                result['num'] = offset + 1 + num
                result['is_even'] = num % 2 != 0
            context['results'] = results
            context['total_results'] = estimated_results
            context['first_result'] = offset + 1
            context['last_result'] = min(offset + RESULTS_PER_PAGE,
                                         estimated_results)
            context['has_previous'] = offset != 0
            if context['has_previous']:
                context['previous_offset'] = offset - RESULTS_PER_PAGE
            context['has_next'] = (estimated_results >
                                   offset + RESULTS_PER_PAGE)
            if context['has_next']:
                context['next_offset'] = offset + RESULTS_PER_PAGE
    else:
        context['has_results'] = False
    return render_to_response('results.html', context)


def handler500(request):
    context = DEFAULT_CONTEXT.copy()
    return render_to_response('500.html', context)
