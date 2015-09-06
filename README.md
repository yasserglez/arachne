Arachne
=======

[![Build Status](https://travis-ci.org/yasserglez/arachne.svg?branch=master)](https://travis-ci.org/yasserglez/arachne)

Arachne is a search engine for files and directories shared via FTP
and similar protocols.

Installation
------------

To install Arachne, make sure you have Python 2.5 and the Python
bindings for Xapian (provided by the `python-xapian` Debian/Ubuntu
package) installed. Then run `python setup.py install` at the terminal
prompt.

Although it is not required, you should consider installing a DNS
cache server (such as the provided by the `djbdns` or `pdnsd`
Debian/Ubuntu packages) in the host running Arachne to speed up the
DNS queries.

See `django/README.md` for instructions to install the Django
application.

Authors
-------

* Yasser González Fernández
* Ariel Hernández Amador

Arachne was inspired by FTP Locate, which was created by Andy Teijelo
Pérez. See also `THANKS.md` for a list of other people who have
contributed to the project.
