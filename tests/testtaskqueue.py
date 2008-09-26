#!/usr/bin/env python
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

import os
import sys
import time
import shutil
import optparse
import unittest
import itertools

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.abspath(os.path.join(TESTDIR, os.path.pardir))
sys.path.insert(0, SRCDIR)

from aracne.utils.url import URL
from aracne.index.error import EmptyQueueError
from aracne.index.task import CrawlTask, TaskQueue


class TestTaskQueue(unittest.TestCase):

    def setUp(self):
        self._dirname = os.path.join(TESTDIR, 'testtaskqueue')
        os.mkdir(self._dirname)
        self._request_wait = 2
        self._error_wait = 4
        self._min_revisit_wait = 2
        self._default_revisit_wait = 4
        self._sites_info = {
            'a78e6853355ad5cdc751ad678d15339382f9ed21':
                {'url': URL('ftp://atlantis.uh.cu/')},
            '7e019d6f671d336a0cc31f137ba034efb13fc327':
                {'url': URL('ftp://andromeda.uh.cu/')},
            'aa958756e769188be9f76fbdb291fe1b2ddd4777':
                {'url': URL('ftp://deltha.uh.cu/')},
            'd4af25db08f5fb6e768db027d51b207cd1a7f5d0':
                {'url': URL('ftp://anduin.uh.cu/')},
            '886b46f54bcd45d4dd5732e290c60e9639b0d101':
                {'url': URL('ftp://tigris.uh.cu/')},
            'ee5b017839d97507bf059ec91f1e5644a30b2fa6':
                {'url': URL('ftp://lara.uh.cu/')},
            '341938200f949daa356e0b62f747580247609f5a':
                {'url': URL('ftp://nimbo.uh.cu/')},
            'd64f2fc98d015a43da3be34668341e3ee6f79133':
                {'url': URL('ftp://liverpool.reduh.uh.cu/')},
            '0d3465f2b9fd5cf55748797c590ea621e3017a29':
                {'url': URL('ftp://london.reduh.uh.cu/')},
            'c5bcce5953866b673054f8927648d634a7237a9b':
                {'url': URL('ftp://bristol.reduh.uh.cu/')},
        }
        self._tasks = {}
        tasks_per_site = 5
        for site_id, info in self._sites_info.iteritems():
            # Set common information.
            info['error_wait'] = self._error_wait
            info['request_wait'] = self._request_wait
            info['min_revisit_wait'] = self._min_revisit_wait
            info['default_revisit_wait'] = self._default_revisit_wait
            # Create tasks for site.
            task_list = []
            for name in (str(n) for n in xrange(tasks_per_site)):
                task_list.append(CrawlTask(site_id, info['url'].join(name)))
            self._tasks[site_id] = task_list
        self._queue = TaskQueue(self._dirname, self._sites_info)

    def test_length(self):
        # It should contain tasks for the root directories.
        num_sites = len(self._sites_info)
        self.assertEquals(len(self._queue), num_sites)
        for i, task in enumerate(itertools.chain(*self._tasks.itervalues())):
            self._queue.put_new(task)
            self.assertEquals(len(self._queue), num_sites + i + 1)
        num_tasks = sum(len(tasks) for tasks in self._tasks.itervalues())
        for i in xrange(num_tasks):
            if i % num_sites == 0 and i != 0:
                time.sleep(self._request_wait)
            task = self._queue.get()
            self._queue.report_done(task)
            self.assertEquals(len(self._queue), num_sites + num_tasks - i - 1)
        # Remove the tasks for the root directories.
        time.sleep(self._request_wait)
        for i in xrange(num_sites):
            self._queue.report_done(self._queue.get())
            self.assertEquals(len(self._queue), num_sites - i - 1)

    def test_populate(self):
        # Remove the tasks for the root directories.
        num_sites = len(self._sites_info)
        for i in xrange(num_sites):
            self._queue.report_done(self._queue.get())
        time.sleep(self._request_wait)
        self.assertRaises(EmptyQueueError, self._queue.get)
        # Insert tasks in the queue.
        for task in itertools.chain(*self._tasks.values()):
            self._queue.put_new(task)
        # Remove tasks for the queue.
        i = 0
        num_tasks = sum(len(tasks) for tasks in self._tasks.itervalues())
        while i < num_tasks:
            if i % num_sites == 0:
                time.sleep(self._request_wait)
            returned = self._queue.get()
            task_list = self._tasks[returned.site_id]
            self.assertEquals(str(returned.url), str(task_list[0].url))
            del task_list[0]
            self._queue.report_done(returned)
            i += 1
        for task_list in self._tasks.itervalues():
            # The lists of tasks should be empty.
            self.assertEquals(len(task_list), 0)

    def test_persist(self):
        for task in itertools.chain(*self._tasks.values()):
            self._queue.put_new(task)
        self._queue.close()
        # It should not return tasks from the removed site.
        del self._sites_info[self._sites_info.keys()[0]]
        self._queue = TaskQueue(self._dirname, self._sites_info)
        i = 0
        num_sites = len(self._sites_info)
        while self._queue:
            if i % (num_sites - 1) == 0:
                time.sleep(self._request_wait)
            returned = self._queue.get()
            self.assertTrue(returned.site_id in self._sites_info)
            self._queue.report_done(returned)
            i += 1

    def test_put_visited(self):
        self._leave_one_task()
        task = self._queue.get()
        self._queue.put_visited(task)
        self._queue.report_done(task)
        time.sleep(self._default_revisit_wait / 2)
        # The task should not be returned yet.
        self.assertRaises(EmptyQueueError, self._queue.get)
        time.sleep(self._default_revisit_wait / 2)
        self.assertEquals(str(task.url), str(self._queue.get().url))

    def test_put_revisited(self):
        self._leave_one_task()
        task = self._queue.get()
        self._queue.put_revisited(task, False)
        self._queue.report_done(task)
        time.sleep(self._min_revisit_wait / 2)
        # The task should not be returned yet.
        self.assertRaises(EmptyQueueError, self._queue.get)
        time.sleep(self._min_revisit_wait / 2)
        self.assertEquals(str(task.url), str(self._queue.get().url))

    def test_report_done(self):
        self._leave_one_task()
        task = self._queue.get()
        self._queue.put_new(task)
        self._queue.report_done(task)
        time.sleep(self._request_wait / 2)
        # The task should not be returned yet.
        self.assertRaises(EmptyQueueError, self._queue.get)
        time.sleep(self._request_wait / 2)
        self.assertEquals(str(task.url), str(self._queue.get().url))

    def test_report_error(self):
        self._leave_one_task()
        task = self._queue.get()
        self._queue.put_new(task)
        self._queue.report_error(task)
        time.sleep(self._error_wait / 2)
        # The task should not be returned yet.
        self.assertRaises(EmptyQueueError, self._queue.get)
        time.sleep(self._error_wait / 2)
        self.assertEquals(str(task.url), str(self._queue.get().url))

    def tearDown(self):
        if os.path.isdir(self._dirname):
            self._queue.close()
            shutil.rmtree(self._dirname)

    def _leave_one_task(self):
        # Remove all the tasks in the queue but one.
        num_sites = len(self._sites_info)
        num_tasks = len(self._queue)
        for i in xrange(num_tasks - 1):
            if i % num_sites == 0 and i != 0:
                time.sleep(self._request_wait)
            self._queue.report_done(self._queue.get())
        self.assertEquals(len(self._queue), 1)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', dest='verbosity', default='2',
                      type='choice', choices=['0', '1', '2'],
                      help='verbosity level: 0 = minimal, 1 = normal, 2 = all')
    options, args = parser.parse_args()
    module = os.path.basename(__file__)[:-3]
    suite = unittest.TestLoader().loadTestsFromName(module)
    runner = unittest.TextTestRunner(verbosity=int(options.verbosity))
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
