import os

from .default import *  # noqa: F403


DEBUG = False

INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405


def custom_show_toolbar(request):
    return True  # Always show toolbar, for example purposes only.


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": custom_show_toolbar,
    "DISABLE_PANELS": {
        "debug_toolbar.panels.profiling.ProfilingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
    },
}


SECRET_KEY = os.environ.get("SECRET_KEY", None)
if SECRET_KEY is None:
    raise Exception("You must set the SECRET_KEY to something secure before running in production or staging.")

ALLOWED_HOSTS = ["aiarena-test.net", "aiarena.net", "*"]

#################################
# Django Storages & django-private-storage configuration #
#################################

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
PRIVATE_STORAGE_CLASS = "private_storage.storage.s3boto3.PrivateS3BotoStorage"

AWS_STORAGE_BUCKET_NAME = os.environ.get("MEDIA_BUCKET")
AWS_PRIVATE_STORAGE_BUCKET_NAME = os.environ.get("MEDIA_BUCKET")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION_NAME = "eu-central-1"
AWS_S3_OBJECT_PARAMETERS = {"ACL": "private"}
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_PRIVATE_S3_ADDRESSING_STYLE = "virtual"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_PRIVATE_S3_SIGNATURE_VERSION = "s3v4"
AWS_PRIVATE_S3_ENCRYPTION = True
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 60 * 60
