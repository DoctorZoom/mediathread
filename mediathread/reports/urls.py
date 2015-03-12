from django.conf.urls import patterns, url

from mediathread.reports.views import SelfRegistrationReportView, \
    ActivityBySchoolView, ActivityByCourseView


urlpatterns = patterns(
    '',
    # urls prefix at root AND 'reports/'

    url(r'^class_assignments/$',
        'mediathread.reports.views.class_assignments',
        name="class-assignments"),
    url(r'^class_assignments/(?P<project_id>\d+)/$',
        'mediathread.reports.views.class_assignment_report',
        name="class-assignment-report"),

    url(r'^class_summary/$',
        'mediathread.reports.views.class_summary',
        name="class-summary"),
    url(r'^class_summary/graph.json$',
        'mediathread.reports.views.class_summary_graph',
        name="class-summary-graph"),

    url(r'^class_activity/$',
        'mediathread.reports.views.class_activity',
        name="class-activity"),

    url(r'^activity/course/$',
        ActivityByCourseView.as_view(),
        name="mediathread-activity-by-course"),

    url(r'^activity/school/$',
        ActivityBySchoolView.as_view(),
        name="mediathread-activity-by-school"),

    url(r'^self-registration/$',
        SelfRegistrationReportView.as_view(),
        name="mediathread-self-registration")
)
