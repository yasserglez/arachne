# -*- coding: utf-8 -*-
#
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

"""Components used to process the crawl results.
"""

import re
import time
import logging
import threading

import xapian

from arachne.task import CrawlTask
from arachne.error import EmptyQueue


class ResultProcessor(object):
    """Result processor.

    Abstract class that should be subclassed by the result processors.
    Instances of subclasses are used by the `ProcessorManager`.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """

    def process(self, result):
        """Process a crawl result.

        If the result is successfully processed the handler should report the
        result as done to the `ResultQueue` using `report_done()`.  When an
        error occurs processing the result the processor should report it to
        the `ResultQueue` using `report_error()` and print a message with
        `logging.error()`.
        """
        raise NotImplementedError('A subclass must override this method.')

    def close(self):
        """Close the processor.
        """


class NaiveProcessor(ResultProcessor):
    """Naive processor.

    This processor only will add a new task to `TaskQueue` for each directory
    entry found in the result.  This can be used to walk the entire directory
    tree.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """
        self._tasks = tasks
        self._results = results

    def process(self, result):
        """Process a crawl result.
        """
        for entry_url, data in result:
            if data['is_dir']:
                task = CrawlTask(result.task.site_id, entry_url)
                self._tasks.put_new(task)
        self._results.report_done(result)


class XapianProcessor(ResultProcessor):
    """Xapian index processor.
    """

    # Term prefixes.
    _IS_DIR_PREFIX = 'D'
    _SITE_ID_PREFIX = 'S'
    _BASENAME_FULL_PREFIX = 'B'
    _BASENAME_TOKEN_PREFIX = 'T'

    # Slots for values.
    _DIRNAME_SLOT = 0
    _BASENAME_SLOT = 1

    # Tags for Boolean properties.
    _IS_DIR_TAG = _IS_DIR_PREFIX + 'is_dir'

    # Attributes used by the _extract_terms() method.
    _MIN_TERM_LENGTH = 2

    _SPLIT_TERM_RE = re.compile(ur'\s+|(?<=\D)[.,]+|[.,]+(?=\D)')

    _BASENAME_TABLE = {}
    for c in u'!"#$%&\'()*+-/:;<=>?@[\]^_`{|}~':
        _BASENAME_TABLE[ord(c)] = u' '

    _TERM_TABLE = {
        ord(u'á') : u'a',
        ord(u'Á') : u'A',
        ord(u'é') : u'e',
        ord(u'É') : u'E',
        ord(u'í') : u'i',
        ord(u'Í') : u'I',
        ord(u'ó') : u'o',
        ord(u'Ó') : u'O',
        ord(u'ú') : u'u',
        ord(u'Ú') : u'U',
        ord(u'ü') : u'u',
        ord(u'Ü') : u'U',
        ord(u'ñ') : u'n',
    }

    class ExactPathDecider(xapian.MatchDecider):
        """Exact path match decider.
        """

        def __init__(self, value):
            xapian.MatchDecider.__init__(self)
            self._value = value

        def __call__(self, doc):
            doc_value = doc.get_value(XapianProcessor._DIRNAME_SLOT)
            doc_value = doc_value.decode('utf-8')
            return doc_value == self._value

    class PrefixPathDecider(xapian.MatchDecider):
        """Path prefix match decider.
        """

        def __init__(self, prefix):
            xapian.MatchDecider.__init__(self)
            self._prefix = prefix

        def __call__(self, doc):
            doc_value = doc.get_value(XapianProcessor._DIRNAME_SLOT)
            doc_value = doc_value.decode('utf-8')
            return doc_value.startswith(self._prefix)

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """
        self._db = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        # Remove documents of old sites from the index (sites removed from the
        # configuration file).
        old_site_ids = [term.term[len(self._SITE_ID_PREFIX):]
                        for term in self._db.allterms(self._SITE_ID_PREFIX)]
        for site_id in sites_info.iterkeys():
            if site_id in old_site_ids:
                old_site_ids.remove(site_id)
        for site_id in old_site_ids:
            self._db.delete_document(self._SITE_ID_PREFIX + site_id)
        self._tasks = tasks
        self._results = results

    def process(self, result):
        """Process a crawl result.
        """
        site_id = result.task.site_id
        # The leading / is required to match prefixes.
        dir_path = result.task.url.path.rstrip(u'/') + u'/'
        doc_count = self._db.get_doccount()
        enquire = xapian.Enquire(self._db)
        enquire.set_query(xapian.Query(self._SITE_ID_PREFIX + site_id))
        # Get all the entries of this directory in the index.
        indexed_entries = []
        decider = self.ExactPathDecider(dir_path)
        for match in enquire.get_mset(0, doc_count, None, decider):
            doc = match.get_document()
            is_dir = self._IS_DIR_TAG in [term.term for term in doc]
            basename = doc.get_value(self._BASENAME_SLOT)
            basename = basename.decode('utf-8')
            try:
                data = result[basename]
            except KeyError:
                # Entry removed from the directory in the site.
                self._db.delete_document(doc.get_docid())
                if is_dir:
                    # Remove entries in the sub-tree of the directory.
                    dirname = doc.get_value(self._DIRNAME_SLOT)
                    dirname = dirname.decode('utf-8')
                    path_prefix = dirname.rstrip(u'/') + u'/' + basename + u'/'
                    decider = self.PrefixPathDecider(path_prefix)
                    for match in enquire.get_mset(0, doc_count, None, decider):
                        doc = match.get_document()
                        self._db.delete_document(doc.get_docid())
            else:
                # If the data is updated remove the entry from the dictionary.
                if is_dir == data['is_dir']:
                    indexed_entries.append(basename)
                else:
                    # Lazy solution.  Remove the document from the index and
                    # then add it again with the right data.
                    self._db.delete_document(doc.get_docid())
        # Add new or modified entries.
        for entry, data in result:
            if entry not in indexed_entries:
                doc = self._create_document(site_id, data)
                self._db.add_document(doc)

    def close(self):
        """Close the processor.
        """
        # There is currently no close() method for xapian databases.
        self._db.flush()

    def _create_document(self, site_id, data):
        """Create and return a Xapian document from `data`.
        """
        url = data['url']
        doc = xapian.Document()
        doc.add_term(self._SITE_ID_PREFIX + site_id, 0)
        if data['is_dir']:
            doc.add_term(self._IS_DIR_TAG, 0)
        doc.add_term(self._BASENAME_FULL_PREFIX + url.basename)
        for token in self._extract_terms(url.basename):
            doc.add_term(self._BASENAME_TOKEN_PREFIX + token)
        # Add more URL properties here if needed.
        doc.add_value(self._DIRNAME_SLOT, url.dirname.rstrip(u'/') + u'/')
        doc.add_value(self._BASENAME_SLOT, url.basename)
        doc.set_data(str(url))
        return doc

    def _extract_terms(self, basename):
        """Extract terms from the basename of a URL.
        """
        # TODO: This surely can be improved.
        terms = []
        basename = basename.translate(self._BASENAME_TABLE)
        for term in self._SPLIT_TERM_RE.split(basename):
            term = term.strip()
            if len(term) >= self._MIN_TERM_LENGTH:
                terms.append(term.lower())
                translated = term.translate(self._TERM_TABLE)
                if translated != term:
                    terms.append(translated.lower())
        return terms


class ProcessorManager(threading.Thread):
    """Processor manager.

    Create and feed the processor.  The processor that will be used is
    currently set in the `__init__()` method but it should be configurable in
    future versions.

    When the `start()` method is invoked it enters in a loop feeding the
    processor with results from the `ResultQueue` until the `stop()` method is
    invoked.  It runs in an independent thread of execution.
    """

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor manager.
        """
        threading.Thread.__init__(self)
        self._sleep = 1
        self._results = results
        self._processor = NaiveProcessor(sites_info, index_dir, tasks, results)
        # Flag used to stop the loop started by the run() method.
        self._running = False

    def run(self):
        """Run the main loop.
        """
        try:
            self._running = True
            while self._running:
                try:
                    result = self._results.get()
                except EmptyQueue:
                    time.sleep(self._sleep)
                else:
                    logging.info('Processing "%s"' % result.task.url)
                    self._processor.process(result)
            self._processor.close()
        except:
            logging.exception('Unhandled exception, printing traceback')

    def stop(self):
        """Order the main loop to end.
        """
        self._running = False
