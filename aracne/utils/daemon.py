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
import signal
import pwd
import grp


# Based on the description found in the Python Cookbook 2nd Edition and the
# implementation of the Living Logic collection of Python modules
# (http://www.livinglogic.de/Python/index.html).


class Daemon(object):
    """Generic UNIX daemon.

    Provides a simple way for creating daemon process in Python.

    It's intended to be subclassed.  You should (at least) override the `run()`
    and (optionally) `terminate()` methods.  If the subclass overrides the
    initializer it must be sure to invoke the base class initializer.  Once a
    `Daemon` instance is created its activity must be started by calling the
    daemon's `start()` method.  This invokes the `run()` method when the
    process is daemonized.  The daemon stops when the process receives a
    SIGTERM signal or the `stop()` method gets invoked and then the
    `terminate()` method is invoked.
    """

    def __init__(self, pidfile=None, stdin='/dev/null', stdout='/dev/null',
                 stderr='/dev/null', user=None, group=None):
        """
        Initializes attributes.

        The `pidfile` argument must be the name of a file.  The `start()`
        method will write the PID of the newly forked daemon to this file.  If
        `pidfile` is `None` no PID is written.

        The `stdin`, `stdout`, and `stderr` arguments are file names that will
        be opened and be used to replace the standard file descriptors in
        `sys.stdin`, `sys.stdout`, and `sys.stderr`.  These arguments are
        optional and default to /dev/null.

        The `user` argument can be the name or uid of a user.  The `start()`
        method will switch to this user for running the daemon.  If `user` is
        `None` no user switching will be done (default).  In the same way
        `group` can be the name or gid of a group.
        """
        self._pidfile = pidfile
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._user = user
        self._group = group

    def start(self):
        """Starts the daemon.

        This methods does all the steps to convert the current process to a
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
        # The pidfile will belong to the new user.
        self._write_pidfile()
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        # Now it's a daemon process.  Invoke run().
        self.run()

    def stop(self):
        """Stops the daemon.

        Removes the pidfile and then invokes the `terminate()` method.
        """
        self._remove_pidfile()
        self.terminate()

    def run(self):
        """Represents the daemon activity.

        You should override this method in a subclass.  It's invoked by the
        `start()` method once the process is a daemon process.
        """

    def terminate(self):
        """Terminates the process.

        This method is responsable of doing any required cleanup (e.g. closing
        connections, file descriptors, etc) and exiting the process
        (e.g. invoke `sys.exit()`).  It gets invoked by the `stop()`
        method. The implementation provided by the `Daemon` class just invokes
        `sys.exit()`), maybe you want to override this.
        """
        sys.exit()

    def _switch_user(self):
        """Switch currrent process user and group ids.

        If `self._user` is `None` and `self._group` is `None` nothing is done.
        `self._user` and `self._group` can be a user/group id (`int`) or a
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

    def _write_pidfile(self):
        """Create the pidfile.

        If `self._pidfile` is `None` nothing is created.
        """
        # TODO: Check for errors.
        if self._pidfile is not None:
            pidfile = open(self._pidfile, 'wb')
            pidfile.write('%d\n' % os.getpid())
            pidfile.close()

    def _remove_pidfile(self):
        """Remove the pidfile.

        If `self._pidfile` is `None` nothing is removed.
        """
        # TODO: Check for errors.
        if self._pidfile is not None:
            os.remove(self._pidfile)

    def _sigterm_handler(self, signum, frame):
        """SIGTERM signal handler.

        Invokes the `stop()` method.
        """
        self.stop()
