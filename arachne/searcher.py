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

"""Index searcher and related classes.
"""

import os

import xapian

from arachne.processor import IndexProcessor


class IndexSearcher(object):
    """Index searcher.
    """

    # Filetype constants used as argument to the search() method.
    SEARCH_ALL = 0
    SEARCH_FILE = 1
    SEARCH_DIRECTORY = 2

    def __init__(self, database_dir):
        """Initialize the searcher.
        """
        index_dir = os.path.join(database_dir, IndexProcessor.INDEX_DIR)
        self._db = xapian.Database(index_dir)
        # Create the stemmers.
        self._stemmers = []
        for lang in IndexProcessor.STEM_LANGS:
            stemmer = xapian.Stem(lang)
            self._stemmers.append(stemmer)

    def get_sites(self):
        """Return the list of indexed sites.

        This method returns a list with a dictionary for each site. Each
        dictionary contains the id of the site (id key) and the URL of the root
        directory (url key).
        """
        doc_count = self._db.get_doccount()
        enquire = xapian.Enquire(self._db)
        enquire.set_docid_order(xapian.Enquire.DONT_CARE)
        query = xapian.Query(IndexProcessor.IS_ROOT_PREFIX
                             + IndexProcessor.TRUE_VALUE)
        enquire.set_query(query)
        sites = []
        for match in enquire.get_mset(0, doc_count):
            doc = match.get_document()
            site = {
                'id': doc.get_value(IndexProcessor.SITE_ID_SLOT).decode('utf-8'),
                'url': doc.get_data().decode('utf-8')
            }
            sites.append(site)
        return sites

    def search(self, query, offset, count, check_at_least, site_ids=(),
               filetype=SEARCH_ALL):
        """Query the index.

        The `query` argument is the user supplied query string. The `sites` and
        `filetype` arguments can be used to restrict the domain of the search.
        """
        if type(query) is not unicode:
            query = query.decode('utf-8')
        enquire = xapian.Enquire(self._db)
        xapian_query = self._parse_query(query, site_ids, filetype)
        enquire.set_query(xapian_query)
        mset = enquire.get_mset(offset, count, check_at_least)
        results = []
        for match in mset:
            result = {}
            doc = match.get_document()
            result['url'] = doc.get_data().decode('utf-8')
            value = doc.get_value(IndexProcessor.IS_DIR_SLOT).decode('utf-8')
            result['is_dir'] = (value == IndexProcessor.TRUE_VALUE)
            results.append(result)
        estimated_total = mset.get_matches_estimated()
        return (estimated_total, results)

    def _parse_query(self, query, site_ids, filetype):
        """Parse the query string and return a Xapian query.
        """
        # Parse the query string.
        plus_terms = set()
        minus_terms = set()
        normal_terms = set()
        for query_term in query.split():
            query_term = query_term.strip()
            if query_term.startswith('+'):
                query_term = query_term[1:]
                if query_term:
                    plus_terms.update(IndexProcessor.get_terms(query_term))
            elif query_term.startswith('-'):
                query_term = query_term[1:]
                if query_term:
                    minus_terms.update(IndexProcessor.get_terms(query_term))
            else:
                if query_term:
                    normal_terms.update(IndexProcessor.get_terms(query_term))
        # Build the queries for plus, minus and normal terms.
        if plus_terms:
            plus_terms = [IndexProcessor.BASENAME_PREFIX + plus_term
                          for plus_term in plus_terms]
            plus_query = xapian.Query(xapian.Query.OP_AND, plus_terms)
        else:
            plus_query = None
        if minus_terms:
            minus_terms = [IndexProcessor.BASENAME_PREFIX + minus_term
                           for minus_term in minus_terms]
            minus_query = xapian.Query(xapian.Query.OP_OR, minus_terms)
        else:
            minus_query = None
        if normal_terms:
            basename_terms = [IndexProcessor.BASENAME_PREFIX + normal_term
                              for normal_term in normal_terms]
            basename_query = xapian.Query(xapian.Query.OP_OR, basename_terms)
            basename_query = xapian.Query(xapian.Query.OP_SCALE_WEIGHT,
                                          basename_query, 10)
            dirname_terms = [IndexProcessor.DIRNAME_PREFIX + normal_term
                             for normal_term in normal_terms]
            dirname_query = xapian.Query(xapian.Query.OP_OR, dirname_terms)
            dirname_query = xapian.Query(xapian.Query.OP_SCALE_WEIGHT,
                                         dirname_query, 2)
            normal_query = xapian.Query(xapian.Query.OP_OR, basename_query,
                                        dirname_query)
        else:
            normal_query = None
        # Stem normal terms.
        stemmed_terms = set()
        for term in normal_terms:
            for stemmer in self._stemmers:
                stemmed_terms.add(stemmer(term))
        # Build the query for the stemmed terms.
        if stemmed_terms:
            stemmed_terms = [IndexProcessor.STEM_PREFIX + stemmed_term
                             for stemmed_term in stemmed_terms]
            stemmed_query = xapian.Query(xapian.Query.OP_OR, stemmed_terms)
        else:
            stemmed_query = None
        # Build the query for the given filetype.
        if filetype == self.SEARCH_FILE:
            filetype_query = xapian.Query(IndexProcessor.IS_DIR_PREFIX
                                          + IndexProcessor.FALSE_VALUE)
        elif filetype == self.SEARCH_DIRECTORY:
            filetype_query = xapian.Query(IndexProcessor.IS_DIR_PREFIX
                                          + IndexProcessor.TRUE_VALUE)
        else:
            filetype_query = None
        # Build the query for the sites.
        if site_ids:
            site_ids_terms = [IndexProcessor.SITE_ID_PREFIX + site_id
                              for site_id in site_ids]
            site_ids_query = xapian.Query(xapian.Query.OP_OR, site_ids_terms)
        else:
            site_ids_query = None
        # Build the final query from the sub-queries.
        query = None
        if plus_query:
            query = plus_query
        if normal_query:
            common_query = xapian.Query(xapian.Query.OP_OR,
                                        normal_query, stemmed_query)
            if query is not None:
                query = xapian.Query(xapian.Query.OP_AND_MAYBE,
                                     query, common_query)
            else:
                query = common_query
        if minus_query:
            if query is not None:
                query = xapian.Query(xapian.Query.OP_AND_NOT,
                                     query, minus_query)
            else:
                query = xapian.Query(xapian.Query.OP_AND_NOT,
                                     xapian.Query(''), minus_query)
        # Query without terms? Return a query that generate an empty MSet.
        if query is None:
            query = xapian.Query()
        else:
            # Apply filters for site and filetype.
            if site_ids_query:
                query = xapian.Query(xapian.Query.OP_FILTER,
                                     query, site_ids_query)
            if filetype_query:
                query = xapian.Query(xapian.Query.OP_FILTER,
                                     query, filetype_query)
        return query
