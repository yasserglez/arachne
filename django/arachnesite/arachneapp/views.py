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

"""Django views for the Arachne application.
"""

import logging

from django.conf import settings
from django.shortcuts import render_to_response

from arachne import __version__
from arachne.searcher import IndexSearcher


if settings.ARACHNE_SEARCH_LOG:
    logging.basicConfig(filename=settings.ARACHNE_SEARCH_LOG,
                        level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


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
    query = request.GET.get('query', request.POST.get('query', ''))
    context['query'] = query
    if query:
        search_type = request.POST.get('searchtype', 'basic')
        context['search_type'] = search_type
        offset = int(request.POST.get('offset', 0))
        # Ensure valid page links, at least, for the next page.
        check_at_least = offset + (2 * RESULTS_PER_PAGE)
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
            context['total_results'] = 0
        # Print a log message if logging is enabled.
        if settings.ARACHNE_SEARCH_LOG and offset == 0:
            logging.info('%s searched for "%s" getting %s results' %
                         (request.META['REMOTE_ADDR'], query,
                          context['total_results']))
    else:
        context['has_results'] = False
        context['total_results'] = 0
    return render_to_response('results.html', context)


def opensearch(request):
    """Serve OpenSearch description.
    """
    context = DEFAULT_CONTEXT.copy()
    if request.META['SERVER_PORT'] == '80':
        server_host = 'http://%s' % request.META['SERVER_NAME']
    else:
        server_host = 'http://%s:%s' % (request.META['SERVER_NAME'],
                                        request.META['SERVER_PORT'])
    context['server_host'] = server_host
    response = render_to_response('opensearch.xml', context)
    response['Content-Type'] = 'application/opensearchdescription+xml'
    return response


def handler500(request):
    """Handler for 500 HTTP errors.
    """
    context = DEFAULT_CONTEXT.copy()
    return render_to_response('500.html', context)


def handler404(request):
    """Handler for 404 HTTP errors.
    """
    context = DEFAULT_CONTEXT.copy()
    return render_to_response('404.html', context)
