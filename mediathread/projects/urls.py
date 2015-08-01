from django.conf.urls import patterns, url

from mediathread.projects.views import ProjectCreateView, ProjectDeleteView, \
    ProjectSortView, SelectionAssignmentView, \
    SelectionAssignmentEditView


urlpatterns = patterns(
    'mediathread.projects.views',

    url(r'^create/$', ProjectCreateView.as_view(), {}, "project-create"),

    url(r'^view/(?P<project_id>\d+)/$',
        'project_workspace',
        name='project-workspace'),

    url(r'^view/(?P<project_id>\d+)/(?P<feedback>\w+)/$',
        'project_workspace',
        name='project-workspace-feedback'),

    url(r'^view/sa/(?P<project_id>\d+)/$',
        SelectionAssignmentView.as_view(), {},
        'selection-assignment-view'),

    url(r'^edit/sa/(?P<project_id>\d+)/$',
        SelectionAssignmentEditView.as_view(), {},
        'selection-assignment-edit'),

    url(r'^save/(?P<project_id>\d+)/$', 'project_save', name='project-save'),

    url(r'^save/(?P<project_id>\d+)/$', 'project_save', name='project-save'),

    url(r'^export/msword/(?P<project_id>\d+)/$',
        'project_export_msword',
        name='project-export-msword'),

    url(r'^export/html/(?P<project_id>\d+)/$',
        'project_export_html',
        name='project-export-html'),

    url(r'^delete/(?P<project_id>\d+)/$',
        ProjectDeleteView.as_view(), {}, 'project-delete'),

    url(r'^reparent/(?P<assignment_id>\d+)/(?P<composition_id>\d+)/$',
        'project_reparent',
        name='project-reparent'),

    url(r'^revisions/(?P<project_id>\d+)/$',
        'project_revisions',
        name='project-revisions'),

    # view versioned read only
    url(r'^view/(?P<project_id>\d+)/version/(?P<version_number>\d+)/$',
        'project_view_readonly', name='project-view-readonly'),

    # instructor information reorder
    url(r'^sort/$', ProjectSortView.as_view(), name='project-sort'),

    # view public url - read only view.
    # Note: StructuredCollaboration requires
    # 1. Url structure must be <classname>/<instance_id>/
    # 2. Name must be <class>-view to do a reverse
    url(r'^(?P<project_id>\d+)/', 'project_view_readonly', name='project-view')
)
