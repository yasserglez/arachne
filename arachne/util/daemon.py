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

# Based on the description found in the Python Cookbook 2nd Edition and the
# implementation of the Living Logic collection of Python modules
# (http://www.livinglogic.de/Python/index.html).

"""Base class to create UNIX daemon processes.
"""

import os
import sys
import signal
import pwd
import grp


class Daemon(object):
    """Generic UNIX daemon.

    This class provides a simple way for creating daemon processes in Python.

    It's intended to be subclassed.  You should (at least) override the `run()`
    and (optionally) `terminate()` methods.  If the subclass overrides the
    initializer it must be sure to invoke the base class initializer.  Once a
    `Daemon` instance is created its activity must be started by calling the
    daemon's `start()` method.  This invokes the `run()` method when the
    process is daemonized.  The daemon stops when the process receives a
    SIGTERM signal and then the `terminate()` method is invoked.
    """

    def __init__(self, pid_file=None, stdin='/dev/null', stdout='/dev/null',
                 stderr='/dev/null', user=None, group=None):
        """
        Initialize attributes.

        The `pid_file` argument must be the name of a file.  The `start()`
        method will write the PID of the newly forked daemon to this file.  If
        `pid_file` is `None` no PID is written.

        The `stdin`, `stdout`, and `stderr` arguments are file names that will
        be opened and be used to replace the standard file descriptors in
        `sys.stdin`, `sys.stdout`, and `sys.stderr`.  These arguments are
        optional and default to /dev/null.

        The `user` argument can be the name or UID of a user.  The `start()`
        method will switch to this user for running the daemon.  If `user` is
        `None` no user switching will be done (default).  In the same way
        `group` can be the name or GID of a group.
        """
        self._pid_file = pid_file
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._user = user
        self._group = group

    def start(self):
        """Start the daemon.

        This method does all the steps to convert the current process to a
        daemon process and then invokes the `run()` method.
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit()
        except OSError, error:
            sys.exit('Error: %s\n' % error.strerror)
        os.setsid()
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit()
        except OSError, error:
            sys.exit('Error: %s\n' % error.strerror)
        os.chdir('/')
        os.umask(0)
        self._switch_user()
        self._redirect_streams()
        # The PID file will belong to the new user.
        self._write_pid_file()
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        # Now it's a daemon process.  Invoke run().
        self.run()
        # When the run() method returns the daemon should stop.
        self._remove_pid_file()

    def run(self):
        """This method represents the daemon activity.

        You should override this method in a subclass.  It's invoked by the
        `start()` method once the process is a daemon process.
        """

    def terminate(self):
        """Order the daemon to stop.

        This method should order to stop the main loop of the daemon.  It gets
        invoked when the SIGTERM signal is received.
        """

    def _switch_user(self):
        """Switch current process user and group ID.

        If `self._user` is `None` and `self._group` is `None` nothing is done.
        `self._user` and `self._group` can be a user/group ID (`int`) or a
        user/group name (`str`).
        """
        # TODO: Check for errors.
        if self._group is not None:
            if isinstance(self._group, basestring):
                gid = grp.getgrnam(self._group).gr_gid
            else:
                gid = self._group
            os.setgid(gid)
        if self._user is not None:
            if isinstance(self._user, basestring):
                uid = pwd.getpwnam(self._user).pw_uid
            else:
                uid = self._user
            os.setuid(uid)
            if 'HOME' in os.environ:
                os.environ['HOME'] = pwd.getpwuid(uid).pw_dir

    def _redirect_streams(self):
        """Redirect standard file descriptors.

        Redirect the standard file descriptors stdin, stdout and stderr to the
        files specified by `self._stdin`, `self._stdout` and `self._stderr`.
        """
        # TODO: Check for errors.
        sys.stdout.flush()
        sys.stderr.flush()
        stdin = open(self._stdin, 'r')
        stdout = open(self._stdout, 'a+')
        stderr = open(self._stderr, 'a+', 0)
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())

    def _write_pid_file(self):
        """Create the PID file.

        If `self._pid_file` is `None` nothing is created.
        """
        # TODO: Check for errors.
        if self._pid_file is not None:
            pid_file = open(self._pid_file, 'wb')
            pid_file.write('%d\n' % os.getpid())
            pid_file.close()

    def _remove_pid_file(self):
        """Remove the PID file.

        If `self._pid_file` is `None` nothing is removed.
        """
        # TODO: Check for errors.
        if self._pid_file is not None:
            os.remove(self._pid_file)

    def _sigterm_handler(self, signum, frame):
        """SIGTERM signal handler.

        Invoke the `terminate()` method.
        """
        self.terminate()
