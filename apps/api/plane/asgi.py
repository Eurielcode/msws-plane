# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.production")

# Initialize Django once, after selecting the settings module. Creating a
# second ASGI application can duplicate Django startup work in each Gunicorn
# worker and leaves the first initialization dependent on inherited settings.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({"http": django_asgi_app})
