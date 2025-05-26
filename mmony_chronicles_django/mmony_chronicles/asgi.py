"""
ASGI config for mmony_chronicles project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmony_chronicles.settings')

application = get_asgi_application()