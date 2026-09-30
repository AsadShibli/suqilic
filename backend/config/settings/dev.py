from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
if "sqlite" in DATABASES["default"]["ENGINE"]:  # noqa: F405
    DATABASES["default"].setdefault("OPTIONS", {})["timeout"] = 20  # noqa: F405
