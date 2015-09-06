Arachne
=======

Arachne is a search engine for files and directories shared via FTP
and similar protocols.

Installation
------------

To install Arachne, make sure you have Python 2.5 and the Python
bindings for Xapian (provided by the `python-xapian` Debian/Ubuntu
package) installed. Then run this at the terminal prompt:

```
python setup.py install
```

Although it is not required, you should consider installing a DNS
cache server (such as the provided by the `djbdns` or `pdnsd`
Debian/Ubuntu packages) in the host running Arachne to speed up
the DNS queries.

See `django/README.md` for instructions to install the Django
application for Arachne.

Authors
-------

* Yasser González Fernández <ygonzalezfernandez@gmail.com>
* Ariel Hernández Amador <gnuaha7@gmail.com>

Arachne was inspired by Andy Teijelo's FTP Locate. See also
`THANKS.md` for a list of other people who have contributed
to the project.
