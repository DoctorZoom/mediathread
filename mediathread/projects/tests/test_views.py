#pylint: disable-msg=R0904
from django.contrib.auth.models import User
from django.test import TestCase
from mediathread.projects.models import Project
import json


class ProjectViewTest(TestCase):
    fixtures = ['unittest_sample_course.json',
                'unittest_sample_projects.json']

    def test_project_save_doesnotexist(self):
        self.assertTrue(
            self.client.login(username='test_student_one', password='test'))

        # Does not exist
        response = self.client.post('/project/save/100/',
                                    {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)

    def test_project_save_cannot_edit(self):
        self.assertTrue(
            self.client.login(username='test_instructor', password='test'))

        # Forbidden to save or view
        response = self.client.post('/project/save/1/',
                                    follow=True,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(len(response.redirect_chain), 1)
        elt = response.redirect_chain[0]
        self.assertTrue(elt[0].endswith('project/view/1/'))
        self.assertEquals(elt[1], 302)

    def test_project_save_nonajax(self):
        self.assertTrue(
            self.client.login(username='test_student_one', password='test'))

        response = self.client.post('/project/save/1/')
        self.assertEquals(response.status_code, 405)

    def test_project_save_valid(self):
        user = User.objects.get(username="test_student_one")

        project = Project.objects.get(id=1)
        self.assertTrue(project.author.username, "test_student_one")
        self.assertEquals(project.title, "Private Composition")

        self.assertTrue(self.client.login(username='test_student_one',
                                          password='test'))

        data = {u'body': [u'<p>abcdefghi</p>'],
                u'participants': [user.id],
                u'publish': [u'PrivateEditorsAreOwners'],
                u'title': [u'Private Student Essay']}

        response = self.client.post('/project/save/1/',
                                    data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        the_json = json.loads(response.content)
        self.assertEquals(the_json["status"], "success")
        self.assertFalse(the_json["is_assignment"])
        self.assertEquals(the_json["title"], "Private Student Essay")
        self.assertEquals(the_json["revision"]["id"], 2)
        self.assertEquals(the_json["revision"]["visibility"], "Private")
        self.assertIsNone(the_json["revision"]["public_url"])
        self.assertEquals(the_json["revision"]["due_date"], "")

    def test_project_save_invalid_title(self):
        user = User.objects.get(username="test_student_one")

        project = Project.objects.get(id=1)
        self.assertTrue(project.author.username, "test_student_one")
        self.assertEquals(project.title, "Private Composition")

        self.assertTrue(self.client.login(username='test_student_one',
                                          password='test'))

        data = {u'body': [u'<p>abcdefghi</p>'],
                u'participants': [user.id],
                u'publish': [u'PrivateEditorsAreOwners'],
                u'title': [u'']}

        response = self.client.post('/project/save/1/',
                                    data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        the_json = json.loads(response.content)
        self.assertEquals(the_json["status"], "error")
        self.assertTrue(the_json["msg"].startswith(' "" is not valid'))

    def test_project_create_and_save(self):
        user = User.objects.get(username="test_student_one")

        self.assertTrue(self.client.login(username='test_student_one',
                                          password='test'))

        data = {u'participants': [user.id],
                u'publish': [u'PrivateEditorsAreOwners']}

        response = self.client.post('/project/create/', data, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(response.redirect_chain[0][0].startswith(
            'http://testserver/project/view/'))

        project = Project.objects.get(title='Untitled')
        self.assertEquals(project.versions.count(), 1)
        self.assertIsNone(project.submitted_date())

        data = {u'body': [u'<p>abcdefghi</p>'],
                u'participants': [user.id],
                u'publish': [u'InstructorShared'],
                u'title': [u'Student Essay']}

        response = self.client.post('/project/save/1/',
                                    data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

        project = Project.objects.get(title='Student Essay')
        self.assertEquals(project.versions.count(), 2)
        self.assertIsNotNone(project.submitted_date())
