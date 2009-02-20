# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009 Yasser González Fernández <yglez@uh.cu>
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

"""Django settings for the Arachne site.
"""

# Debug settings. Set this to False in a production environment.
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.  If
# running in a Windows environment this must be set to the same as your system
# time zone.
TIME_ZONE = 'America/Havana'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-es'

# If you set this to False, Django will make some optimizations so as not to
# load the internationalization machinery.
USE_I18N = False

# Full name of the URLconf root module.
ROOT_URLCONF = 'arachnesite.urls'

# List of strings representing installed apps.
INSTALLED_APPS = (
    'arachnesite.arachneapp',
)

# Add the path to the directory with the templates here.
TEMPLATE_DIRS = (
)

# We don't need any context processor.
TEMPLATE_CONTEXT_PROCESSORS = ()

# This site does not need any middleware but leave this as sugested in the
# Django documentation.
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

# Absolute path to the database directory. This should match the value in
# /etc/arachne/daemon.conf.
ARACHNE_DATABASE_DIR = '/var/lib/arachne'

# Absolute path to a file where the search log should be located.  If set to an
# empty string logging is disabled.
ARACHNE_SEARCH_LOG = ''

# Path, from the root of the site, where the Arachne site is located.
ARACHNE_ROOT = '/'

# URL where the Arachne media is located. The leading / is required!
ARACHNE_MEDIA_URL = '/media/'
