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

"""Protocol handlers.
"""

# Before creating any socket, set the default timeout for all
# sockets. Currently there is no way to specify timeout values using the
# urllib, urllib2 and ftplib interfaces. This should change in future Python
# releases.
import socket
socket.setdefaulttimeout(5 * 60)

import os
import re
import errno
import ftplib
import urllib
import urllib2
import logging
import htmlentitydefs

from arachne import __version__
from arachne.result import CrawlResult


class ProtocolHandler(object):
    """Protocol handler.

    Abstract class that should be subclassed by all supported protocols in the
    crawler.  This provides a way to extend the crawler to support new
    protocols.  Instances of this class are used by the `SiteCrawler`.

    The subclasses should set the `name` class attribute.
    """

    name = ''

    def __init__(self, sites_info, tasks, results):
        """Initialize the protocol handler.

        The `sites_info` argument will be a dictionary mapping site ID to the
        information for the sites.  This can be useful to support advanced
        settings for a site (e.g. proxy server).
        """

    def execute(self, task):
        """Execute a task.

        If the task is successfully executed the handler should put the result
        in the `ResultQueue` and report the task as done to the `TaskQueue`
        using the `report_done()`.  When an error occurs the handler should
        report it to the `TaskQueue` using `report_error()` and print a message
        with `logging.error()`.
        """
        raise NotImplementedError('A subclass must override this method.')


class FileHandler(ProtocolHandler):
    """Handler for local files.
    """

    name = 'file'

    def __init__(self, sites_info, tasks, results):
        """Initialize handler.
        """
        self._tasks = tasks
        self._results = results
        self._errnos_dir = (errno.EACCES, )

    def execute(self, task):
        """Execute the task and return the result.
        """
        url = task.url
        try:
            if os.path.isdir(url.path):
                result = CrawlResult(task, True)
                for entry_name in os.listdir(url.path):
                    data = {}
                    entry_url = url.join(entry_name)
                    data['is_dir'] = os.path.isdir(entry_url.path)
                    result.add_entry(entry_url.basename, data)
            else:
                result = CrawlResult(task, False)
        except OSError, error:
            if error.errno in self._errnos_dir:
                self._tasks.report_error_dir(task)
            else:
                self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (%s)' % (url, error.strerror))
        except IOError, error:
            self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (%s)' % (url, error.strerror))
        else:
            self._results.put(result)
            self._tasks.report_done(task)


class FTPHandler(ProtocolHandler):
    """Handler for FTP sites.
    """

    name = 'ftp'

    def __init__(self, sites_info, tasks, results):
        """Initialize the handler.
        """
        self._encoding = 'utf-8'
        self._tasks = tasks
        self._results = results

    def execute(self, task):
        """Execute the task and return the result.
        """
        url = task.url
        try:
            ftp = ftplib.FTP()
            if url.port:
                ftp.connect(url.hostname.encode(self._encoding), url.port)
            else:
                ftp.connect(url.hostname.encode(self._encoding))
            if url.username:
                ftp.login(url.username.encode(self._encoding),
                          url.password.encode(self._encoding))
            else:
                ftp.login()
            try:
                ftp.cwd(url.path.encode(self._encoding))
            except ftplib.error_perm:
                # Failed to change directory.
                result = CrawlResult(task, False)
            else:
                # It seems to be a valid directory.
                result = CrawlResult(task, True)
                entries = []
                callback = lambda line: entries.append(self._parse_list(line))
                ftp.retrlines('LIST', callback)
                for entry_name, is_dir in (entry for entry in entries
                                           if entry is not None):
                    data = {}
                    if is_dir is not None:
                        data['is_dir'] = is_dir
                    else:
                        # The parser does not known if this entry is a
                        # directory or not.  Try to change directory, if error,
                        # assume it is a file.
                        try:
                            entry_url = url.join(entry_name)
                            ftp.cwd(entry_url.path.encode(self._encoding))
                        except ftplib.error_perm:
                            data['is_dir'] = False
                        else:
                            data['is_dir'] = True
                    if not data['is_dir']:
                        content = self._get_content(str(task.url.join(entry_name)))
                        if content:
                            data['content'] = content
                    result.add_entry(entry_name, data)
            ftp.quit()
        except socket.timeout, error:
            self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (%s)' % (url, error))
        except socket.error, error:
            self._tasks.report_error_site(task)
            if not isinstance(error, basestring):
                error = error[1]
            logging.error('Error visiting "%s" (%s)' % (url, error))
        except IOError, error:
            self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (%s)' % (url, error.strerror))
        except EOFError:
            ftp.close()
            self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (Error reading data)' % url)
        except ftplib.Error, error:
            try:
                ftp.quit()
            except ftplib.Error:
                ftp.close()
            except (IOError, EOFError, socket.timeout, socket.error):
                # Ignore possible exceptions executing QUIT.
                pass
            self._tasks.report_error_dir(task)
            msg = 'Error visiting "%s" (%s)' % (url, str(error).strip())
            logging.error(msg)
        else:
            self._results.put(result)
            self._tasks.report_done(task)

    @staticmethod
    def _parse_list(line):
        """Parse lines from a LIST response.

        `None` is returned if could not parse the line, otherwise it returns a
        tuple containing the name of the item and a Boolean value indicating if
        it is a directory.  The Boolean value will be `None` if the parse could
        not known if the item is a directory or not.
        """
        # Based on ftpparse.c and ftpparse.h by D. J. Bernstein.
        if line.startswith(tuple('-dbclps')):
            # UNIX-style listing.
            try:
                if line[0] == '-':
                    is_dir = False
                elif line[0] == 'd':
                    is_dir = True
                else:
                    is_dir = None
                data = line.split(None, 8)
                if len(data) == 9:
                    if line[0] == 'l':
                        name = data[-1].split(' -> ')[0]
                    else:
                        name = data[-1]
                else:
                    raise ValueError('Invalid line format.')
            except ValueError:
                return None
            else:
                return (name, is_dir)
        elif line.startswith(tuple('0123456789')):
            # MSDOS format.
            try:
                line  = line[17:].lstrip()
                if line.startswith('<DIR>'):
                    is_dir = True
                    name = line[15:]
                else:
                    is_dir = False
                    name = line[line.index(' ') + 1:]
            except (IndexError, ValueError):
                return None
            else:
                return (name, is_dir)
        elif line.startswith('+'):
            # Easily Parsed LIST Format.
            try:
                facts, name = line[1:].split('\t')
                facts = facts.split(',')
                is_dir = '/' in facts
            except IndexError:
                return None
            else:
                return (name, is_dir)
        else:
            # Could not parse the line.  Maybe because the format is unknown
            # format or it contains additional information provided by the FTP
            # server that can be ignored.
            return None

    @staticmethod
    def _get_content(url):
        """Get the UTF-8 text to be indexed as the content of the file.
        """
        return u''

class FTPContentHandler(FTPHandler):
    """A proof-of-concept FTP handler.

    This class extends the FTP handler to support downloading the files
    to index its content. Currently only the metadata of MP3 files
    is indexed.
    """

    name = 'ftp_content'

    def __init__(self, sites_info, tasks, results):
        super(FTPContentHandler, self).__init__(sites_info, tasks, results)

    @staticmethod
    def _get_content(url):
        """Get the UTF-8 text to be indexed as the content of the file.
        """
        content = u''
        if url.lower().endswith(u'.mp3'):
            try:
                import tempfile
                from mutagen.easyid3 import EasyID3
                # Download the file.
                remote_handler = urllib2.urlopen(url)
                local_handler = tempfile.NamedTemporaryFile(delete = False)
                local_name = local_handler.name
                local_handler.write(remote_handler.read())
                local_handler.close()
                remote_handler.close()
                # Extract the metadata.
                metadata = []
                audio = EasyID3(local_name)
                for tag in (u'artist', u'album', u'title'):
                    try:
                        metadata.extend(audio[tag])
                    except:
                        pass
                os.remove(local_name)
                content = u' '.join(metadata)
            except Exception:
                pass
        return content


class ApacheHandler(ProtocolHandler):
    """Handler for sites using Apache autoindex.
    """

    name = 'apache'

    _ENTRIES_RE = re.compile(r'alt="\[([^\]]+)\]".+<a[^>]+>([^<]+?)/?</a>.*[0-9]{2}-[a-zA-Z]{3}-[0-9]{4}', re.I)

    _ENTITIES_RE = re.compile(r'&(\w+?);')

    def __init__(self, sites_info, tasks, results):
        """Initialize the handler.
        """
        self._encoding = 'utf-8'
        self._tasks = tasks
        self._results = results

    def execute(self, task):
        """Execute the task and return the result.
        """
        url = task.url
        encoded_url = str(url)
        path_encoded = url.path.encode(self._encoding)
        encoded_url = '%s%s/' % (encoded_url[:-len(path_encoded)],
                                 urllib.quote(path_encoded.rstrip('/')))
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Arachne/%s' % __version__)]
        try:
            handler = opener.open(encoded_url)
            data = handler.read()
            # Everything seems to be OK, add entries to the result.
            result = CrawlResult(task, True)
            for match in self._ENTRIES_RE.finditer(data):
                entry_data = {}
                entry_data['is_dir'] = (match.group(1).lower() == 'dir')
                entry_name = self._ENTITIES_RE.sub(self._sub_entity, match.group(2))
                result.add_entry(entry_name, entry_data)
            handler.close()
            self._results.put(result)
            self._tasks.report_done(task)
        except urllib2.HTTPError, error:
            if error.code == 404:
                # The directory does not exists. Generate a not-found result
                # because the entire directory tree should be removed from the
                # index.
                result = CrawlResult(task, False)
                self._results.put(result)
                self._tasks.report_done(task)
            else:
                self._tasks.report_error_dir(task)
                logging.error('Error visiting "%s" (%s: %s)' % (url, error.code, error.msg))
        except urllib2.URLError, error:
            self._tasks.report_error_site(task)
            reason = error.reason
            if not isinstance(reason, basestring):
                try:
                    reason = reason[1]
                except IndexError:
                    reason = str(reason)
            logging.error('Error visiting "%s" (%s)' % (url, reason))
        except EOFError:
            handler.close()
            self._tasks.report_error_site(task)
            logging.error('Error visiting "%s" (Error reading data)' % url)

    @staticmethod
    def _sub_entity(match):
        """Callback used to substitute HTML entities.
        """
        try:
            return htmlentitydefs.entitydefs[match.group(1)]
        except KeyError:
            return match.group(0)
