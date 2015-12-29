# flake8: noqa
from mediathread.settings import *

locals().update(
    common(
        project=project,
        base=base,
        INSTALLED_APPS=INSTALLED_APPS,
        STATIC_ROOT=STATIC_ROOT,
        s3static=False,
    ))

TEMPLATE_DIRS += [
    "/var/www/mediathread/mediathread/mediathread/deploy_specific/templates",
]

try:
    from local_settings import *
except ImportError:
    pass
