# Django settings for mediathread project.

# if you add a 'deploy_specific' directory
# then you can put a settings.py file and templates/ overrides there
# (see bottom)

import os.path
import re
from ccnmtlsettings.shared import common

project = 'mediathread'
base = os.path.dirname(__file__)

locals().update(common(project=project, base=base))

PROJECT_APPS = [
    'mediathread.main',
    'mediathread.djangosherd',
    'mediathread.assetmgr',
    'mediathread.projects',
    'mediathread.reports',
    'mediathread.discussions',
    'mediathread.taxonomy',
    'structuredcollaboration',
]

CACHE_BACKEND = 'locmem:///'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 3600  # One Hour
    }
}

TEMPLATE_CONTEXT_PROCESSORS += [  # noqa
    'django.contrib.messages.context_processors.messages',
    'mediathread.main.views.django_settings',
]

MIDDLEWARE_CLASSES += [  # noqa
    'corsheaders.middleware.CorsMiddleware',
    'courseaffils.middleware.CourseManagerMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

TEMPLATE_DIRS.insert(0, os.path.join(base, "deploy_specific/templates"))  # noqa

INSTALLED_APPS += [  # noqa
    'courseaffils',
    'tagging',
    'structuredcollaboration',
    'mediathread.assetmgr',
    'mediathread.djangosherd',
    'mediathread.projects',
    'mediathread.discussions',
    'threadedcomments',
    'django_comments',
    'djangohelpers',
    'mediathread.reports',
    'mediathread.main',
    'mediathread.taxonomy',
    'registration',
    'corsheaders',
    'reversion',
    'lti_auth',
    'bootstrap3',
]

THUMBNAIL_SUBDIR = "thumbs"
SERVER_EMAIL = "mediathread@example.com"

DATE_FORMAT = DATETIME_FORMAT = "g:i a, m/d/y"
LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# for AuthRequirementMiddleware. this should be a list of
# url prefixes for paths that can be accessed by anonymous
# users. we need to allow anonymous access to the login
# page, and to static resources.

ANONYMOUS_PATHS = (
    '/media/',
    '/accounts/',
    '/admin/',
    '/help/',
    '/api/user/courses',
)

NON_ANONYMOUS_PATHS = (
    '/analysis/',
    '/annotations/',
    '/api/',
    '/archive/',
    '/asset/',
    '/assignment/',
    '/comments/',
    '/dashboard/',
    '/discussion/',
    '/explore/',
    '/impersonate/',
    '/project/',
    '/reports/',
    '/setting/',
    '/taxonomy/',
    '/upgrade/',
    '/upload/',
    re.compile(r'^/$'),
)

# save is an exception, for server2server api
COURSEAFFILS_PATHS = NON_ANONYMOUS_PATHS + ('/save', '/settings')

COURSEAFFILS_EXEMPT_PATHS = ANONYMOUS_PATHS
COURSEAFFIL_AUTO_MAP_GROUPS = ['demo']

COMMENTS_ALLOW_PROFANITIES = True
COMMENTS_APP = 'threadedcomments'
COMMENT_MAX_LENGTH = None

FORCE_LOWERCASE_TAGS = True

# specify FLICKR api key as a string
# https://www.flickr.com/services/api/misc.api_keys.html
DJANGOSHERD_FLICKR_APIKEY = 'undefined'

# specify YouTube browser api key as a string
# obtain a browser api key here:
# https://developers.google.com/youtube/registering_an_application#Create_API_Keys
YOUTUBE_BROWSER_APIKEY = 'undefined'

BOOKMARKLET_VERSION = '2'

# Mediathread instantiates a Flowplayer .swf to play many video flavors.
# Update this variable with your site's Flowplayer installation
# See README.markdown for more information
# expected: http://<server>/<directory>/flowplayer-3.2.18.swf
FLOWPLAYER_SWF_LOCATION = None
FLOWPLAYER_HTML5_LOCATION = None
# Specify your own plugin versions here. The player looks in the same
# http://<server>/<directory>/ specified above.
FLOWPLAYER_AUDIO_PLUGIN = 'flowplayer.audio-3.2.11.swf'
FLOWPLAYER_PSEUDOSTREAMING_PLUGIN = 'flowplayer.pseudostreaming-3.2.13.swf'
FLOWPLAYER_RTMP_PLUGIN = 'flowplayer.rtmp-3.2.13.swf'

DEFAULT_COLLABORATION_POLICY = 'InstructorManaged'


# this gets around Django 1.2's stupidity for commenting
# we're already checking that the request is from someone in the class
def no_reject(request, reason):
    request.csrf_processing_done = True
    return None

CSRF_FAILURE_VIEW = no_reject

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

ACCOUNT_ACTIVATION_DAYS = 7

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ('GET',)
CORS_ALLOW_CREDENTIALS = True


def default_url_processor(url, label=None, request=None):
    return url

ASSET_URL_PROCESSOR = default_url_processor

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'lti_auth.auth.LTIBackend',
]

LTI_TOOL_CONFIGURATION = {
    'title': 'Mediathread',
    'description': 'View and filter your Mediathread selections. '
    'A new icon will show up in your course rich editor letting you '
    'search and filter your Mediathread selections and click to '
    'embed selections in your course material.',
    'launch_url': 'lti/',
    'embed_url': 'asset/embed/',
    'embed_icon_url': 'media/img/icons/icon-16.png',
    'embed_tool_id': 'mediathread',
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

# if you add a 'deploy_specific' directory
# then you can put a settings.py file and templates/ overrides there
# otherwise, make sure you specify the correct database settings in your
# local_settings.py
try:
    from mediathread.deploy_specific.settings import *  # noqa
    if 'EXTRA_INSTALLED_APPS' in locals():
        INSTALLED_APPS = INSTALLED_APPS + EXTRA_INSTALLED_APPS
except:
    pass
