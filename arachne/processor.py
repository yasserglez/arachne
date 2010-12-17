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

"""Components used to process the crawl results.
"""

import os
import re
import time
import threading
import logging

import xapian

from arachne.error import EmptyQueue
from arachne.task import CrawlTask


class ResultProcessor(object):
    """Result processor.

    Abstract class that should be subclassed by the result processors.
    Instances of subclasses are used by the `ProcessorManager`.
    """

    def __init__(self, sites_info, databse_dir, tasks, results):
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

    def flush(self):
        """Flush to disc the modifications.
        """

    def close(self):
        """Close the processor.
        """


class NaiveProcessor(ResultProcessor):
    """Naive result processor.

    This processor only will add a new task to `TaskQueue` for each directory
    entry found in the result.  This can be used to walk the entire directory
    tree.
    """

    def __init__(self, sites_info, database_dir, tasks, results):
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


class IndexProcessor(ResultProcessor):
    """Index result processor.
    """

    # Name of the directory containing the Xapian index.
    INDEX_DIR = 'index'

    # Term prefixes.
    SITE_ID_PREFIX = u'S'
    IS_DIR_PREFIX = u'I'
    IS_ROOT_PREFIX = u'R'
    BASENAME_PREFIX = u'B'
    DIRNAME_PREFIX = u'D'
    STEM_PREFIX = u'Z'
    CONTENT_PREFIX = u'C'

    # Boolean values for terms and values.
    FALSE_VALUE = u'0'
    TRUE_VALUE = u'1'

    # Values slots.
    SITE_ID_SLOT = 0
    IS_DIR_SLOT = 1
    IS_ROOT_SLOT = 2
    BASENAME_SLOT = 3
    DIRNAME_SLOT = 4
    PATH_SLOT = 5

    # Stemming languages.
    STEM_LANGS = (u'en', u'es')

    # Attributes used by the get_terms() method.
    _MIN_TERM_LENGTH = 3

    _VALID_SHORT_TERMS = (u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8',
                          u'9', u'c', u'C')

    _SPLIT_RE = re.compile(ur'\s+|(?<=\D)[.,]+|[.,]+(?=\D)')

    _CAMEL_CASE_RE = re.compile(ur'(?<=[a-zA-Z])(?=[A-Z][a-z])')

    _WHITE_SPACE_RE = re.compile(ur'(?<=\d)(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)')

    _WHITE_SPACE_TRANSLATION = {}
    for c in u'!"#$%&\'()*+-/:;<=>?@[\]^_`{|}~':
        _WHITE_SPACE_TRANSLATION[ord(c)] = u' '

    _TERM_TRANSLATION = {
        ord(u'á'): u'a',
        ord(u'Á'): u'A',
        ord(u'é'): u'e',
        ord(u'É'): u'E',
        ord(u'í'): u'i',
        ord(u'Í'): u'I',
        ord(u'ó'): u'o',
        ord(u'Ó'): u'O',
        ord(u'ú'): u'u',
        ord(u'Ú'): u'U',
        ord(u'ü'): u'u',
        ord(u'Ü'): u'U',
        ord(u'ñ'): u'n',
    }

    def __init__(self, sites_info, database_dir, tasks, results):
        """Initialize the processor.
        """
        self._tasks = tasks
        self._results = results
        index_dir = os.path.join(database_dir, self.INDEX_DIR)
        self._db = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        # Create the stemmers.
        self._stemmers = []
        for lang in self.STEM_LANGS:
            stemmer = xapian.Stem(lang)
            self._stemmers.append(stemmer)
        # Remove documents of old sites from the index.
        old_site_ids = [term.term[len(self.SITE_ID_PREFIX):]
                        for term in self._db.allterms(self.SITE_ID_PREFIX)]
        for site_id in sites_info.iterkeys():
            if site_id in old_site_ids:
                old_site_ids.remove(site_id)
        for site_id in old_site_ids:
            self._db.delete_document(self.SITE_ID_PREFIX + site_id)

    def process(self, result):
        """Process a crawl result.
        """
        url = result.task.url
        site_id = result.task.site_id
        if not result.found:
            self._rmtree(site_id, url.path)
        else:
            enquire = xapian.Enquire(self._db)
            enquire.set_docid_order(xapian.Enquire.DONT_CARE)
            site_id_query = xapian.Query(self.SITE_ID_PREFIX + site_id)
            if url.is_root:
                # The parent of the root directory is not known, or it can even
                # not exist. We should check that the root directory is indexed
                # because it is required to search for files in a selected
                # number of sites.
                root_query = xapian.Query(self.IS_ROOT_PREFIX + self.TRUE_VALUE)
                query = xapian.Query(xapian.Query.OP_FILTER, site_id_query,
                                     root_query)
                enquire.set_query(query)
                mset = enquire.get_mset(0, 1)
                if mset.empty():
                    # Index this root directory.
                    data = {'url': url, 'is_dir': True}
                    doc = self._create_document(site_id, data)
                    self._db.add_document(doc)
            # Process entries of the directory.
            dir_changed = False
            doc_count = self._db.get_doccount()
            # Get all the entries of this directory in the index.
            dirname = url.path.rstrip(u'/') + u'/'
            dirname_query = xapian.Query(xapian.Query.OP_VALUE_RANGE,
                                         self.DIRNAME_SLOT, dirname, dirname)
            query = xapian.Query(xapian.Query.OP_FILTER, site_id_query,
                                 dirname_query)
            enquire.set_query(query)
            indexed_entries = []
            for match in enquire.get_mset(0, doc_count):
                doc = match.get_document()
                is_dir = self._get_doc_value(doc, self.IS_DIR_SLOT)
                basename = self._get_doc_value(doc, self.BASENAME_SLOT)
                # I check this as an ugly hack to avoid removing the root
                # directory of the site if we are processing the result for the
                # root directory itself.
                if basename != '/':
                    try:
                        data = result[basename]
                    except KeyError:
                        # Entry removed from the directory in the site.
                        dir_changed = True
                        if is_dir:
                            # Remove entries in the sub-tree of the directory.
                            self._rmtree(site_id, dirname + basename + u'/')
                        else:
                            self._db.delete_document(doc.get_docid())
                    else:
                        # Check if metadata is updated.
                        if is_dir == data['is_dir']:
                            indexed_entries.append(basename)
                        else:
                            dir_changed = True
                            # Lazy solution.  Remove the document from the
                            # index and then add it again with the right data.
                            self._db.delete_document(doc.get_docid())
            # Add new or modified entries.
            for entry, data in result:
                if entry not in indexed_entries:
                    # New entry found in the directory. Mark as changed, index
                    # the entry and if it is a directory add a new task to
                    # visit it.
                    dir_changed = True
                    doc = self._create_document(site_id, data)
                    self._db.add_document(doc)
                    if data['is_dir']:
                        task = CrawlTask(result.task.site_id, data['url'])
                        self._tasks.put_new(task)
            # Put a new task to visit the directory again.
            self._tasks.put_visited(result.task, dir_changed)
        # Result sucessfully processed.
        self._results.report_done(result)

    def flush(self):
        """Flush to disc the modifications.
        """
        self._db.flush()

    def close(self):
        """Close the processor.
        """
        # There is currently no close() method for Xapian databases.
        self._db.flush()
        del self._db

    def _rmtree(self, site_id, dirpath):
        """Remove documents for entries in the given directory tree. The
        document of the root of the directory tree is also removed.
        """
        enquire = xapian.Enquire(self._db)
        enquire.set_docid_order(xapian.Enquire.DONT_CARE)
        site_id_query = xapian.Query(self.SITE_ID_PREFIX + site_id)
        # Remove document of the directory itself.
        path_query = xapian.Query(xapian.Query.OP_VALUE_RANGE,
                                  self.PATH_SLOT, dirpath, dirpath)
        query = xapian.Query(xapian.Query.OP_FILTER, site_id_query, path_query)
        enquire.set_query(query)
        for match in enquire.get_mset(0, self._db.get_doccount()):
            doc = match.get_document()
            self._db.delete_document(doc.get_docid())
        # Remove documents of the decendants.
        dirname_start = dirpath.rstrip(u'/') + u'/'
        dirname_end = dirname_start + u'\U0010ffff'
        dirname_query = xapian.Query(xapian.Query.OP_VALUE_RANGE,
                                     self.DIRNAME_SLOT, dirname_start,
                                     dirname_end)
        query = xapian.Query(xapian.Query.OP_FILTER, site_id_query,
                             dirname_query)
        enquire.set_query(query)
        for match in enquire.get_mset(0, self._db.get_doccount()):
            doc = match.get_document()
            self._db.delete_document(doc.get_docid())

    def _get_doc_value(self, doc, slot):
        """Return the value stored at the given slot.
        """
        value = doc.get_value(slot).decode('utf-8')
        if slot == self.IS_DIR_SLOT or slot == self.IS_ROOT_SLOT:
            value = (value == self.TRUE_VALUE)
        return value

    @classmethod
    def get_terms(cls, path):
        """Extract terms from the given path.

        This algorithm treats the slashes correctly, so, the path can be
        absolute or relative.
        """
        terms = set()
        path = path.translate(cls._WHITE_SPACE_TRANSLATION)
        path = cls._WHITE_SPACE_RE.sub(u' ', path)
        for term in cls._SPLIT_RE.split(path):
            term = term.strip()
            if (len(term) >= cls._MIN_TERM_LENGTH
                or term in cls._VALID_SHORT_TERMS):
                terms.add(term.lower())
                # Add translated terms.
                translated = term.translate(cls._TERM_TRANSLATION)
                terms.add(translated.lower())
                # Add camel cased words.
                words = cls._CAMEL_CASE_RE.sub(u' ', translated).split(u' ')
                for word in words:
                    word = word.strip()
                    if (len(word) >= cls._MIN_TERM_LENGTH
                        or word in cls._VALID_SHORT_TERMS):
                        terms.add(word.lower())
        return terms

    def _create_document(self, site_id, data):
        """Create and return a Xapian document from `data`.
        """
        url = data['url']
        doc = xapian.Document()
        doc.add_term(self.SITE_ID_PREFIX + site_id)
        doc.add_value(self.SITE_ID_SLOT, site_id)
        if data['is_dir']:
            doc.add_term(self.IS_DIR_PREFIX + self.TRUE_VALUE)
            doc.add_value(self.IS_DIR_SLOT, self.TRUE_VALUE)
        else:
            doc.add_term(self.IS_DIR_PREFIX + self.FALSE_VALUE)
            doc.add_value(self.IS_DIR_SLOT, self.FALSE_VALUE)
        if url.is_root:
            doc.add_term(self.IS_ROOT_PREFIX + self.TRUE_VALUE)
            doc.add_value(self.IS_ROOT_SLOT, self.TRUE_VALUE)
        else:
            doc.add_term(self.IS_ROOT_PREFIX + self.FALSE_VALUE)
            doc.add_value(self.IS_ROOT_SLOT, self.FALSE_VALUE)
        stemmed_terms = set()
        for term in self.get_terms(url.basename):
            doc.add_term(self.BASENAME_PREFIX + term)
            for stemmer in self._stemmers:
                stemmed_term = stemmer(term).decode('utf-8')
                stemmed_terms.add(stemmed_term)
        doc.add_value(self.BASENAME_SLOT, url.basename)
        if 'content' in data:
            generator = xapian.TermGenerator()
            for stemmer in self._stemmers:
                generator.set_stemmer(stemmer)
            generator.set_document(doc)
            generator.index_text_without_positions(data['content'], 1, self.CONTENT_PREFIX)
        for term in self.get_terms(url.dirname):
            doc.add_term(self.DIRNAME_PREFIX + term)
            for stemmer in self._stemmers:
                stemmed_term = stemmer(term).decode('utf-8')
                stemmed_terms.add(stemmed_term)
        doc.add_value(self.DIRNAME_SLOT, url.dirname.rstrip(u'/') + u'/')
        for stemmed_term in stemmed_terms:
            doc.add_term(self.STEM_PREFIX + stemmed_term)
        doc.add_value(self.PATH_SLOT, url.path)
        doc.set_data(str(url))
        return doc


class ProcessorManager(threading.Thread):
    """Processor manager.

    Create and feed the processor. The processor that will be used is currently
    set in the `__init__()` method but it should be configurable in future
    versions.

    When the `start()` method is invoked it enters in a loop feeding the
    processor with results from the `ResultQueue` until the `stop()` method is
    invoked. It runs in an independent thread of execution.
    """

    def __init__(self, sites_info, database_dir, tasks, results):
        """Initialize the processor manager.
        """
        threading.Thread.__init__(self)
        self._sleep = 1
        self._results = results
        self._processor = IndexProcessor(sites_info, database_dir, tasks, results)
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
                    self._processor.flush()
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
