from django.conf.urls import patterns, url

urlpatterns = patterns(
    'mediathread.discussions.views',

    url(r'^create/$', 'discussion_create', name='discussion-create'),

    url(r'^delete/(?P<discussion_id>\d+)/$',
        'discussion_delete',
        name='discussion-delete'),

    url(r'^comment/(?P<comment_id>\d+)/$',
        'comment_save',
        name='comment-save'),

    url(r'^(?P<discussion_id>\d+)/$',
        'discussion_view',
        name='discussion-view'),
)
