"""ASGI config for Sectrex."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sectrix.settings")
application = get_asgi_application()
