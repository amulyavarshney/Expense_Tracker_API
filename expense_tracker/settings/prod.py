"""
Production settings — hardened defaults.
"""

import os

from .base import *  # noqa: F403

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in (
    'true',
    '1',
    'yes',
)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
