"""
WSGI config for mmony_chronicles project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmony_chronicles.settings')

application = get_wsgi_application()