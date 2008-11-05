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

import logging
import re
import threading
import time

import xapian

from arachne.error import EmptyQueue
from arachne.task import CrawlTask


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
    """Naive result processor.

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
    """Xapian result processor.
    """

    # Term prefixes.
    _SITE_ID_PREFIX = u'S'
    _IS_DIR_PREFIX = u'I'
    _BASENAME_TERM_PREFIX = u'B'
    _DIRNAME_TERM_PREFIX = u'D'
    _STEM_PREFIX = u'Z'

    # Values for Boolean terms.
    _IS_DIR_FALSE = u'0'
    _IS_DIR_TRUE = u'1'

    # Values slots.
    _BASENAME_FULL_SLOT = 0
    _DIRNAME_FULL_SLOT = 1
    _IS_DIR_SLOT = 2

    # Stemming languages.
    _STEM_LANGS = (u'en', u'es')

    # Attributes used by the _get_terms() method.
    _MIN_TERM_LENGTH = 2

    _VALID_SHORT_TERMS = ('C', 'c')

    _TERM_SPLIT_RE = re.compile(ur'\s+|(?<=\D)[.,]+|[.,]+(?=\D)')

    _TERM_CAMEL_RE = re.compile('(?<=[a-zA-Z])(?=[A-Z][a-z])')

    _PATH_TABLE = {}
    for c in u'!"#$%&\'()*+-/:;<=>?@[\]^_`{|}~':
        _PATH_TABLE[ord(c)] = u' '

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

    def __init__(self, sites_info, index_dir, tasks, results):
        """Initialize the processor.
        """
        self._tasks = tasks
        self._results = results
        self._db = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        # Create the stemmers.
        self._stemmers = []
        for lang in self._STEM_LANGS:
            stemmer = xapian.Stem(lang)
            self._stemmers.append(stemmer)
        # Remove documents of old sites from the index.
        old_site_ids = [term.term[len(self._SITE_ID_PREFIX):]
                        for term in self._db.allterms(self._SITE_ID_PREFIX)]
        for site_id in sites_info.iterkeys():
            if site_id in old_site_ids:
                old_site_ids.remove(site_id)
        for site_id in old_site_ids:
            self._db.delete_document(self._SITE_ID_PREFIX + site_id)

    def process(self, result):
        """Process a crawl result.
        """
        url = result.task.url
        site_id = result.task.site_id
        doc_count = self._db.get_doccount()
        enquire = xapian.Enquire(self._db)
        enquire.set_docid_order(xapian.Enquire.DONT_CARE)
        # Get all the entries of this directory in the index.
        site_id_query = xapian.Query(self._SITE_ID_PREFIX + site_id)
        dirname = url.path.rstrip(u'/') + u'/'
        dirname_query = xapian.Query(xapian.Query.OP_VALUE_RANGE,
                                     self._DIRNAME_FULL_SLOT, dirname,
                                     dirname)
        query = xapian.Query(xapian.Query.OP_FILTER, site_id_query,
                             dirname_query)
        enquire.set_query(query)
        indexed_entries = []
        for match in enquire.get_mset(0, doc_count):
            doc = match.get_document()
            is_dir = self._get_doc_value(doc, self._IS_DIR_SLOT)
            basename = self._get_doc_value(doc, self._BASENAME_FULL_SLOT)
            try:
                data = result[basename]
            except KeyError:
                # Entry removed from the directory in the site.
                if is_dir:
                    # Remove entries in the sub-tree of the directory.
                    dirname_start = dirname + basename + u'/'
                    dirname_end = dirname_start + u'\U0010ffff'
                    dirname_query = xapian.Query(xapian.Query.OP_VALUE_RANGE,
                                                 self._DIRNAME_FULL_SLOT,
                                                 dirname_start, dirname_end)
                    query = xapian.Query(xapian.Query.OP_FILTER, site_id_query,
                                         dirname_query)
                    enquire.set_query(query)
                    for match in enquire.get_mset(0, doc_count):
                        sub_doc = match.get_document()
                        self._db.delete_document(sub_doc.get_docid())
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
        # There is currently no close() method for Xapian databases.
        self._db.flush()

    def _get_doc_value(self, doc, slot):
        """Return the value stored at the given slot.
        """
        value = doc.get_value(slot).decode('utf-8')
        if slot == self._IS_DIR_SLOT:
            value = (value == self._IS_DIR_TRUE)
        return value

    def _get_terms(self, path):
        """Extract terms from the given path.

        This algorithm treats the slashes correctly, so, the path can be
        absolute or relative.
        """
        terms = []
        path = path.translate(self._PATH_TABLE)
        for term in self._TERM_SPLIT_RE.split(path):
            term = term.strip()
            if (len(term) >= self._MIN_TERM_LENGTH
                or term in self._VALID_SHORT_TERMS):
                lower_term = term.lower()
                if lower_term not in terms:
                    terms.append(lower_term)
                # Add translated terms.
                translated = term.translate(self._TERM_TABLE)
                if translated != term:
                    lower_translated = translated.lower()
                    if lower_translated not in terms:
                        terms.append(lower_translated)
                # Add camel cased words.
                words = self._TERM_CAMEL_RE.sub(u' ', translated).split(u' ')
                for word in words:
                    word = word.strip()
                    if len(word) >= self._MIN_TERM_LENGTH:
                        lower_word = word.lower()
                        if lower_word not in terms:
                            terms.append(lower_word)
        return terms

    def _create_document(self, site_id, data):
        """Create and return a Xapian document from `data`.
        """
        url = data['url']
        doc = xapian.Document()
        doc.add_term(self._SITE_ID_PREFIX + site_id, 0)
        if data['is_dir']:
            doc.add_value(self._IS_DIR_SLOT, self._IS_DIR_TRUE)
            doc.add_term(self._IS_DIR_PREFIX + self._IS_DIR_TRUE, 0)
        else:
            doc.add_value(self._IS_DIR_SLOT, self._IS_DIR_FALSE)
            doc.add_term(self._IS_DIR_PREFIX + self._IS_DIR_FALSE, 0)
        stemmed_terms = []
        for term in self._get_terms(url.basename):
            doc.add_term(self._BASENAME_TERM_PREFIX + term)
            for stemmer in self._stemmers:
                stemmed_term = stemmer(term).decode('utf-8')
                if stemmed_term not in stemmed_terms:
                    stemmed_terms.append(stemmed_term)
        for term in self._get_terms(url.dirname):
            doc.add_term(self._DIRNAME_TERM_PREFIX + term)
            for stemmer in self._stemmers:
                stemmed_term = stemmer(term).decode('utf-8')
                if stemmed_term not in stemmed_terms:
                    stemmed_terms.append(stemmed_term)
        for stemmed_term in stemmed_terms:
            doc.add_term(self._STEM_PREFIX + stemmed_term)
        doc.add_value(self._BASENAME_FULL_SLOT, url.basename)
        doc.add_value(self._DIRNAME_FULL_SLOT, url.dirname.rstrip(u'/') + u'/')
        doc.set_data(str(url))
        return doc


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
