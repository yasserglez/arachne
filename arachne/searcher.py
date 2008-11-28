# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
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

"""Index searcher.
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

        This method returns a list with a tuple containing the id and the URL
        of the root directory for each indexed site.
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
            site_id = doc.get_value(IndexProcessor.SITE_ID_SLOT)
            url = doc.get_data()
            sites.append((site_id.decode('utf-8'), url.decode('utf-8')))
        return sites

    def search(self, query, sites=(), filetype=SEARCH_ALL):
        """Query the index.

        The `query` argument is the user supplied query as string. The `sites`
        and `filetype` arguments can be used to restrict the domain of the
        search.
        """
