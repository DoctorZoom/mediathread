from django.conf.urls import patterns, url

from mediathread.discussions.views import DiscussionView, DiscussionDeleteView


urlpatterns = patterns(
    'mediathread.discussions.views',

    url(r'^create/$', 'discussion_create', name='discussion-create'),

    url(r'^delete/(?P<discussion_id>\d+)/$',
        DiscussionDeleteView.as_view(), {},
        name='discussion-delete'),

    url(r'^comment/(?P<comment_id>\d+)/$',
        'comment_save',
        name='comment-save'),

    url(r'^(?P<discussion_id>\d+)/$',
        DiscussionView.as_view(), {}, 'discussion-view'),

)
