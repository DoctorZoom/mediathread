import json

from courseaffils.lib import in_course_or_404, get_public_name
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.template.defaultfilters import slugify
from django.views.generic.base import View, TemplateView
from djangohelpers.lib import allow_http

from mediathread.api import CourseResource
from mediathread.api import UserResource
from mediathread.discussions.views import threaded_comment_json
from mediathread.djangosherd.models import SherdNote
from mediathread.mixins import (
    LoggedInMixin, RestrictedMaterialsMixin, AjaxRequiredMixin,
    JSONResponseMixin, LoggedInFacultyMixin, ProjectVisibleMixin,
    ProjectEditableMixin)
from mediathread.projects.admin import ProjectVersion
from mediathread.projects.api import ProjectResource
from mediathread.projects.forms import ProjectForm
from mediathread.projects.models import Project
from mediathread.taxonomy.api import VocabularyResource
from mediathread.taxonomy.models import Vocabulary


class ProjectCreateView(LoggedInMixin, JSONResponseMixin, View):

    def post(self, request):
        project_type = request.POST.get('project_type', 'composition')
        due_date = request.POST.get('due_date', None)
        title = project_type = request.POST.get('title', Project.DEFAULT_TITLE)
        project = Project.objects.create(author=request.user,
                                         course=request.course,
                                         title=title,
                                         project_type=project_type,
                                         due_date=due_date)

        project.participants.add(request.user)

        item_id = request.POST.get('item', None)
        project.create_or_update_item(item_id)

        policy = request.POST.get('publish', 'PrivateEditorsAreOwners')
        project.create_or_update_collaboration(policy)

        if not request.is_ajax():
            return HttpResponseRedirect(project.get_absolute_url())
        else:
            is_faculty = request.course.is_faculty(request.user)
            can_edit = project.can_edit(request.course, request.user)

            resource = ProjectResource(record_viewer=request.user,
                                       is_viewer_faculty=is_faculty,
                                       editable=can_edit)
            project_context = resource.render_one(request, project)
            project_context['editing'] = True

            data = {'panel_state': 'open',
                    'template': 'project',
                    'context': project_context}

            return self.render_to_json_response(data)


class ProjectSaveView(LoggedInMixin, AjaxRequiredMixin, JSONResponseMixin,
                      ProjectEditableMixin, View):

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs.get('project_id', None))
        policy = request.POST.get('publish', 'PrivateEditorsAreOwners')

        frm = ProjectForm(request, instance=project, data=request.POST)
        if frm.is_valid():
            frm.instance.submitted = policy != 'PrivateEditorsAreOwners'
            frm.instance.author = request.user
            frm.save()

            frm.instance.participants.add(request.user)

            item_id = request.POST.get('item', None)
            frm.instance.create_or_update_item(item_id)

            # update the collaboration
            frm.instance.create_or_update_collaboration(policy)

            ctx = {
                'status': 'success',
                'is_assignment': frm.instance.is_assignment(),
                'title': frm.instance.title,
                'context': {
                    'project': {
                        'url': frm.instance.get_absolute_url()
                    }
                },
                'revision': {
                    'id': frm.instance.get_latest_version(),
                    'public_url': frm.instance.public_url(),
                    'visibility': project.visibility_short(),
                    'due_date': project.get_due_date()
                }
            }
        else:
            ctx = {'status': 'error', 'msg': ""}
            for key, value in frm.errors.items():
                if key == '__all__':
                    ctx['msg'] = ctx['msg'] + value[0] + "\n"
                else:
                    ctx['msg'] = \
                        '%s "%s" is not valid for the %s field.\n %s\n' % \
                        (ctx['msg'], frm.data[key],
                         frm.fields[key].label,
                         value[0].lower())

        return self.render_to_json_response(ctx)


class ProjectDeleteView(LoggedInMixin, ProjectEditableMixin, View):
    def post(self, request, *args, **kwargs):
        """
        Delete the requested project. Regular access conventions apply.
        If the logged-in user is not allowed to delete
        the project, an HttpResponseForbidden
        will be returned
        """
        project = get_object_or_404(Project, pk=kwargs.get('project_id', None))
        project.delete()

        return HttpResponseRedirect('/')


@login_required
def project_reparent(request, assignment_id, composition_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("forbidden")

    try:
        assignment = Project.objects.get(id=assignment_id)
    except Project.DoesNotExist:
        return HttpResponseServerError("Invalid assignment parameter")

    try:
        composition = Project.objects.get(id=composition_id)
    except Project.DoesNotExist:
        return HttpResponseServerError("Invalid composition parameter")

    if assignment.is_assignment():
        parent_collab = assignment.get_collaboration()
        parent_collab.append_child(composition)

    return HttpResponseRedirect('/')


@login_required
def project_revisions(request, project_id):
    project = get_object_or_404(Project, pk=project_id, course=request.course)

    if not project.is_participant(request.user):
        return HttpResponseForbidden("forbidden")

    data = {}
    data['revisions'] = [{
        'version_number': v.version_number,
        'versioned_id': v.versioned_id,
        'author': get_public_name(v.instance().author, request),
        'modified': v.modified.strftime("%m/%d/%y %I:%M %p")}
        for v in project.versions.order_by('-change_time')]

    return HttpResponse(json.dumps(data, indent=2),
                        content_type='application/json')


@allow_http("GET")
def project_view_readonly(request, project_id, version_number=None):
    """
    A single panel read-only view of the specified project/version combination.
    No assignment, response or feedback access/links.
    Regular access conventions apply. For example, if the project is "private"
    an HTTPResponseForbidden will be returned.

    Used for reviewing old project versions and public project access.

    Keyword arguments:
    project_id -- the model id
    version_number -- a specific project version or
    None for the current version

    """

    project = get_object_or_404(Project, pk=project_id)

    if not project.can_read(request.course, request.user):
        return HttpResponseForbidden("forbidden")

    data = {'space_owner': request.user.username}

    course = request.course
    if not course:
        # public view
        course = request.collaboration_context.content_object
        public_url = project.public_url()
    else:
        # versioned view
        public_url = reverse('project-view-readonly',
                             kwargs={'project_id': project.id,
                                     'version_number': version_number})

    if not request.is_ajax():
        data['project'] = project
        data['version'] = version_number
        data['public_url'] = public_url
        return render_to_response('projects/project.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        if version_number:
            version = get_object_or_404(ProjectVersion,
                                        versioned_id=project_id,
                                        version_number=version_number)

            project = version.instance()

        panels = []

        # Requested project, either assignment or composition
        request.public = True

        resource = ProjectResource(record_viewer=request.user,
                                   is_viewer_faculty=False,
                                   editable=False)
        project_context = resource.render_one(request, project, version_number)
        panel = {'panel_state': 'open',
                 'panel_state_label': "Version View",
                 'context': project_context,
                 'template': 'project'}
        panels.append(panel)

        data['panels'] = panels

        return HttpResponse(json.dumps(data, indent=2),
                            content_type='application/json')


class ProjectWorkspaceView(LoggedInMixin, ProjectVisibleMixin,
                           JSONResponseMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs.get('project_id', None))

        if project.is_selection_assignment():
            return self.selection_assignment(project)
        else:
            return self.default_project(project, args, kwargs)

    def selection_assignment(self, project):
        self.template_name = 'projects/selection_assignment_view.html'
        ctx = {
            'project': project,
            'can_edit': project.can_edit(self.request.course,
                                         self.request.user)
        }
        return self.render_to_response(ctx)

    def default_project(self, project, *args, **kwargs):
        """
        A multi-panel editable view for the specified project
        Legacy note: Ideally, this function would be named project_view but
        StructuredCollaboration requires the view name
        to be  <class>-view to do a reverse lookup

        Panel 1: Parent Assignment (if applicable)
        Panel 2: Project
        Panel 3: Instructor Feedback (if applicable & exists)

        Keyword arguments:
        project_id -- the model id
        """
        request = self.request
        show_feedback = kwargs.get('feedback', None) == "feedback"
        data = {'space_owner': request.user.username,
                'show_feedback': show_feedback}

        if not request.is_ajax():
            self.template_name = 'projects/project.html'
            data['project'] = project
            return self.render_to_response(data)
        else:
            panels = []

            vocabulary = VocabularyResource().render_list(
                request, Vocabulary.objects.get_for_object(request.course))

            owners = UserResource().render_list(request,
                                                request.course.members)

            is_faculty = request.course.is_faculty(request.user)
            can_edit = project.can_edit(request.course, request.user)
            feedback_discussion = project.feedback_discussion() \
                if is_faculty or can_edit else None

            # Project Parent (assignment) if exists
            parent = project.assignment()
            if parent:
                pedit = parent.can_edit(request.course, request.user)
                resource = ProjectResource(
                    record_viewer=request.user, is_viewer_faculty=is_faculty,
                    editable=pedit)
                ctx = resource.render_one(request, parent)
                state = "open" if (project.is_empty()) else "closed"

                panel = {'is_faculty': is_faculty,
                         'panel_state': state,
                         'subpanel_state': 'closed',
                         'context': ctx,
                         'owners': owners,
                         'vocabulary': vocabulary,
                         'template': 'project'}
                panels.append(panel)

            # Requested project, can be either an assignment or composition
            resource = ProjectResource(record_viewer=request.user,
                                       is_viewer_faculty=is_faculty,
                                       editable=can_edit)
            project_context = resource.render_one(request, project)

            # only editing if it's new
            project_context['editing'] = \
                True if can_edit and len(project.body) < 1 else False

            project_context['create_instructor_feedback'] = \
                is_faculty and parent and not feedback_discussion

            panel = {'is_faculty': is_faculty,
                     'panel_state': 'closed' if show_feedback else 'open',
                     'context': project_context,
                     'template': 'project',
                     'owners': owners,
                     'vocabulary': vocabulary}
            panels.append(panel)

            # Project Response -- if the requested project is an assignment
            # This is primarily a student view. The student's response should
            # pop up automatically when the parent assignment is viewed.
            if project.is_assignment():
                responses = project.responses_by(request.course, request.user,
                                                 request.user)
                if len(responses) > 0:
                    response = responses[0]
                    response_can_edit = response.can_edit(request.course,
                                                          request.user)
                    resource = ProjectResource(record_viewer=request.user,
                                               is_viewer_faculty=is_faculty,
                                               editable=response_can_edit)
                    response_context = resource.render_one(request, response)

                    panel = {'is_faculty': is_faculty,
                             'panel_state': 'closed',
                             'context': response_context,
                             'template': 'project',
                             'owners': owners,
                             'vocabulary': vocabulary}
                    panels.append(panel)

                    if not feedback_discussion and response_can_edit:
                        feedback_discussion = response.feedback_discussion()

            data['panels'] = panels

            # If feedback exists for the requested project
            if feedback_discussion:
                # 3rd pane is the instructor feedback, if it exists
                panel = {'panel_state': 'open' if show_feedback else 'closed',
                         'panel_state_label': "Instructor Feedback",
                         'template': 'discussion',
                         'owners': owners,
                         'vocabulary': vocabulary,
                         'context': threaded_comment_json(request,
                                                          feedback_discussion)}
                panels.append(panel)

            # Create a place for asset editing
            panel = {'panel_state': 'closed',
                     'panel_state_label': "Item Details",
                     'template': 'asset_quick_edit',
                     'update_history': False,
                     'owners': owners,
                     'vocabulary': vocabulary,
                     'context': {'type': 'asset'}}
            panels.append(panel)

            return self.render_to_json_response(data)


@login_required
@allow_http("GET")
def project_export_html(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not project.can_read(request.course, request.user):
        return HttpResponseForbidden("forbidden")

    template = loader.get_template("projects/export.html")

    context = RequestContext(request, {
        'space_owner': request.user.username,
        'project': project,
        'body': project.body})

    return HttpResponse(template.render(context))


@login_required
@allow_http("GET")
def project_export_msword(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not project.can_read(request.course, request.user):
        return HttpResponseForbidden("forbidden")

    template = loader.get_template("projects/msword.html")

    body = SherdNote.objects.fully_qualify_references(project.body,
                                                      request.get_host())
    body = body.replace("padding-left", "margin-left")

    context = RequestContext(request, {
        'space_owner': request.user.username,
        'project': project,
        'body': body})

    response = HttpResponse(template.render(context),
                            content_type='application/vnd.ms-word')
    response['Content-Disposition'] = \
        'attachment; filename=%s.doc' % (slugify(project.title))
    return response


class ProjectDetailView(LoggedInMixin, RestrictedMaterialsMixin,
                        AjaxRequiredMixin, JSONResponseMixin,
                        ProjectVisibleMixin, View):

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        can_edit = project.can_edit(request.course, request.user)

        resource = ProjectResource(record_viewer=request.user,
                                   is_viewer_faculty=self.is_viewer_faculty,
                                   editable=can_edit)
        context = resource.render_one(request, project)
        return self.render_to_json_response(context)


class ProjectCollectionView(LoggedInMixin, RestrictedMaterialsMixin,
                            AjaxRequiredMixin, JSONResponseMixin, View):
    """
    An ajax-only request to retrieve assets for a course or a specified user
    Example:
        /api/project/user/sld2131/
        /api/project/
    """

    def get(self, request):
        ures = UserResource()
        course_res = CourseResource()
        pres = ProjectResource(editable=self.viewing_own_records,
                               record_viewer=self.record_viewer,
                               is_viewer_faculty=self.is_viewer_faculty)
        assignments = []

        ctx = {
            'space_viewer': ures.render_one(request, self.record_viewer),
            'editable': self.viewing_own_records,
            'course': course_res.render_one(request, request.course),
            'is_faculty': self.is_viewer_faculty
        }

        if (self.record_owner):
            in_course_or_404(self.record_owner.username, request.course)

            projects = Project.objects.visible_by_course_and_user(
                request.course, request.user, self.record_owner,
                self.viewing_faculty_records)

            # Show unresponded assignments if viewing self & self is a student
            if not self.is_viewer_faculty and self.viewing_own_records:
                assignments = Project.objects.unresponded_assignments(
                    request.course, request.user)

            ctx['space_owner'] = ures.render_one(request, self.record_owner)
            ctx['assignments'] = pres.render_assignments(request, assignments)
        else:
            projects = Project.objects.visible_by_course(request.course,
                                                         request.user)

        ctx['projects'] = pres.render_projects(request, projects)
        ctx['compositions'] = len(projects) > 0 or len(assignments) > 0

        return self.render_to_json_response(ctx)


class ProjectSortView(LoggedInFacultyMixin, AjaxRequiredMixin,
                      JSONResponseMixin, View):
    '''
    An ajax-only request to update project ordinality. Used by instructors
    to tune the "From Your Instructor" list on the homepage
    '''
    def post(self, request):
        ids = request.POST.getlist("project")
        for idx, project_id in enumerate(ids):
            project = Project.objects.get(id=project_id)
            if idx != project.ordinality:
                project.ordinality = idx
                project.save()

        return self.render_to_json_response({'sorted': 'true'})


class SelectionAssignmentEditView(LoggedInFacultyMixin, ProjectEditableMixin,
                                  TemplateView):
    template_name = 'projects/selection_assignment_edit.html'

    def get_context_data(self, **kwargs):
        project_id = kwargs.get('project_id', None)
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            form = ProjectForm(self.request, instance=project)
        else:
            form = ProjectForm(self.request, instance=None)
        return {'form': form}
