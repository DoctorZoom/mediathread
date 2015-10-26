import urllib
from urlparse import parse_qs, urlparse

from django.test.client import RequestFactory
import oauthlib.oauth1
from oauthlib.oauth1.rfc5849 import CONTENT_TYPE_FORM_URLENCODED


BASE_LTI_PARAMS = {
    u'context_id': u'course-v1:edX+DemoX+Demo_Course',
    u'custom_course_group':
        u't3.y2011.s001.ce0001.aaaa.st.course:columbia.edu',
    u'launch_presentation_return_url': u'',
    u'lis_person_contact_email_primary': u'foo@bar.com',
    u'lis_person_name_full': u'Foo Bar Baz',
    u'lis_result_sourcedid': u'course-v1%3AedX%2BDemoX%2BDemo_Course'
                             u':-724d6c2b5fcc4a17a26b9120a1d463aa:student',
    u'lti_message_type': u'basic-lti-launch-request',
    u'lti_version': u'LTI-1p0',
    u'roles': u'Instructor,Staff',
    u'resource_link_id': u'-724d6c2b5fcc4a17a26b9120a1d463aa',
    u'user_id': u'student',
}

CONSUMERS = {
    '__consumer_key__': {'secret': '__lti_secret__'}
}


def generate_lti_request():
    """
    This code generated valid LTI 1.0 basic-lti-launch-request request
    """
    client = oauthlib.oauth1.Client('__consumer_key__',
                                    client_secret='__lti_secret__',
                                    signature_method=oauthlib.oauth1.
                                    SIGNATURE_HMAC,
                                    signature_type=oauthlib.oauth1.
                                    SIGNATURE_TYPE_QUERY)

    signature = client.sign(
        'http://testserver/lti/',
        http_method='POST', body=urllib.urlencode(BASE_LTI_PARAMS),
        headers={'Content-Type': CONTENT_TYPE_FORM_URLENCODED})

    url_parts = urlparse(signature[0])
    query_string = parse_qs(url_parts.query, keep_blank_values=True)
    verify_params = dict()
    for key, value in query_string.iteritems():
        verify_params[key] = value[0]

    params = BASE_LTI_PARAMS.copy()
    params.update(verify_params)

    request = RequestFactory().post('/lti/', params)
    request.session = {}
    return request
