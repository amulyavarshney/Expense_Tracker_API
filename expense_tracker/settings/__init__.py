"""
Django settings package.

Loads ``dev`` or ``prod`` based on the ``ENV`` environment variable (default: ``dev``).
Set ``DJANGO_SETTINGS_MODULE`` to a specific module (e.g. ``expense_tracker.settings.prod``)
to bypass this selector.
"""

import os

_env = os.environ.get('ENV', 'dev').lower()

if _env in ('prod', 'production'):
    from .prod import *  # noqa: F403
else:
    from .dev import *  # noqa: F403
