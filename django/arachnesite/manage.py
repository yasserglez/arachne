#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Django manage.py script for Arachne site.
"""

from django.core.management import execute_manager

import settings


if __name__ == "__main__":
    execute_manager(settings)
