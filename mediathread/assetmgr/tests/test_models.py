# pylint: disable-msg=R0904
from courseaffils.models import Course
from django.contrib.auth.models import User
from django.test import TestCase
from mediathread.assetmgr.models import Asset, Source
from mediathread.djangosherd.models import SherdNote


class AssetTest(TestCase):
    fixtures = ['unittest_sample_course.json']

    def test_unicode(self):
        asset = Asset.objects.get(title="Mediathread: Introduction")
        self.assertEquals(asset.__unicode__(),
                          'Mediathread: Introduction <1> (Sample Course)')

    def test_metadata(self):
        asset = Asset.objects.get(title="Mediathread: Introduction")
        ctx = asset.metadata()
        self.assertEquals(ctx['author'], [u'CCNMTL'])
        self.assertEquals(ctx['category'], [u'Education'])

        asset = Asset.objects.get(title="MAAP Award Reception")
        ctx = asset.metadata()
        self.assertEquals(len(ctx.keys()), 0)

    def test_video(self):
        # youtube -- asset #1
        asset = Asset.objects.get(id=1)
        self.assertEquals(asset.media_type(), 'video')
        self.assertFalse(asset.primary.is_image())
        self.assertFalse(asset.primary.is_archive())
        self.assertFalse(asset.primary.is_audio())

    def test_image(self):
        # image -- asset #2
        asset = Asset.objects.get(id=2)

        self.assertEquals(asset.media_type(), 'image')
        self.assertTrue(asset.primary.is_image())
        self.assertFalse(asset.primary.is_archive())
        self.assertFalse(asset.primary.is_audio())

    def test_migrate_many(self):
        from_course = Course.objects.get(title="Sample Course")
        faculty = [user.id for user in from_course.faculty.all()]

        course = Course.objects.get(title="Alternate Course")
        self.assertEquals(len(course.asset_set.all()), 1)

        user = User.objects.get(username='test_instructor_two')
        titles = ['Mediathread: Introduction', 'MAAP Award Reception']
        assets = Asset.objects.filter(title__in=titles)

        object_map = {'assets': {}, 'notes': {}}
        object_map = Asset.objects.migrate(
            assets, course, user, faculty, object_map,
            True, True)

        self.assertEquals(len(course.asset_set.all()), 3)
        asset = object_map['assets'][1]
        self.assertNotEquals(asset.id, 1)
        self.assertEquals(asset.title, "Mediathread: Introduction")
        self.assertEquals(asset.course, course)
        self.assertEquals(asset.author, user)
        self.assertEquals(len(asset.sherdnote_set.all()), 5)

        try:
            asset.sherdnote_set.get(title='Whole Item Selection')
            asset.sherdnote_set.get(title='Annotations')
            asset.sherdnote_set.get(title='Manage Sources')
            asset.sherdnote_set.get(title='Video Selection Is Time-based')
        except SherdNote.DoesNotExist:
            self.assertTrue(False)

        gann = asset.global_annotation(user, False)
        self.assertTrue(gann is not None)
        self.assertEquals(
            gann.tags,
            u',youtube, test_instructor_item,test_instructor_two')
        self.assertEquals(
            gann.body,
            u'All credit to Mark and Caseytest_instructor_two notes')

        asset = object_map['assets'][2]
        self.assertNotEquals(asset.id, 2)
        self.assertEquals(asset.title, "MAAP Award Reception")
        self.assertEquals(asset.course, course)
        self.assertEquals(asset.author, user)
        self.assertEquals(len(asset.sherdnote_set.all()), 2)

        try:
            asset.sherdnote_set.get(title='Our esteemed leaders')
        except SherdNote.DoesNotExist:
            self.assertTrue(False)

        gann = asset.global_annotation(user, False)
        self.assertTrue(gann is not None)
        self.assertEquals(gann.tags, u',flickr, instructor_one')
        self.assertEquals(gann.body, u'instructor one item note')

    def test_migrate_one(self):
        asset = Asset.objects.get(id=1)
        self.assertEquals(asset.title, "Mediathread: Introduction")

        new_course = Course.objects.get(title="Alternate Course")

        new_user = User.objects.get(username='test_instructor_alt')

        new_asset = Asset.objects.migrate_one(asset, new_course, new_user)
        self.assertEquals(new_asset.author, new_user)
        self.assertEquals(new_asset.course, new_course)

        self.assertEquals(new_asset.media_type(), 'video')
        self.assertFalse(new_asset.primary.is_image())
        self.assertFalse(new_asset.primary.is_archive())
        self.assertFalse(new_asset.primary.is_audio())

        # migrate a global annotation
        global_annotation = SherdNote.objects.get(id=1)
        global_note = SherdNote.objects.migrate_one(global_annotation,
                                                    new_asset,
                                                    new_user, True, True)
        self.assertTrue(global_note.is_global_annotation())
        self.assertEquals(global_note.author, new_user)
        self.assertEquals(global_note.title, None)
        self.assertEquals(global_note.tags, ',youtube, test_instructor_item')
        self.assertEquals(global_note.body, u'All credit to Mark and Casey')

        # try to migrate another global annotation as well
        # the global annotation that was already created will come back
        another_global_annotation = SherdNote.objects.get(id=20)
        another_note = SherdNote.objects.migrate_one(another_global_annotation,
                                                     new_asset,
                                                     new_user,
                                                     True,
                                                     True)
        self.assertEquals(another_note, global_note)

        selected_annotation = SherdNote.objects.get(id=2)
        new_note = SherdNote.objects.migrate_one(selected_annotation,
                                                 new_asset,
                                                 new_user,
                                                 True,
                                                 True)
        self.assertFalse(new_note.is_global_annotation())
        self.assertEquals(new_note.author, new_user)
        self.assertEquals(new_note.title, 'Manage Sources')
        self.assertEquals(new_note.tags, ',video')
        self.assertEquals(new_note.body, '')

    def test_migrate_one_duplicates(self):
        asset = Asset.objects.get(id=1)
        self.assertEquals(asset.title, "Mediathread: Introduction")

        new_course = Course.objects.get(title="Alternate Course")

        new_user = User.objects.get(username='test_instructor_alt')

        new_asset = Asset.objects.migrate_one(asset, new_course, new_user)
        self.assertEquals(new_asset.author, new_user)
        self.assertEquals(new_asset.course, new_course)

        duplicate_asset = Asset.objects.migrate_one(asset,
                                                    new_course,
                                                    new_user)
        self.assertEquals(new_asset, duplicate_asset)

        selected_annotation = SherdNote.objects.get(id=2)
        new_note = SherdNote.objects.migrate_one(selected_annotation,
                                                 new_asset,
                                                 new_user,
                                                 True,
                                                 True)
        self.assertFalse(new_note.is_global_annotation())
        self.assertEquals(new_note.author, new_user)
        self.assertEquals(new_note.title, 'Manage Sources')

        duplicate_note = SherdNote.objects.migrate_one(selected_annotation,
                                                       new_asset,
                                                       new_user,
                                                       True, True)
        self.assertEquals(new_note, duplicate_note)

    def test_update_reference_in_string(self):
        text = ('<p><a href="/asset/2/annotations/10/">Nice Tie</a>'
                '</p><p><a href="/asset/2/annotations/10/">Nice Tie</a>'
                '</p><p><a href="/asset/2/annotations/8/">Nice Tie</a>'
                '</p><a href="/asset/2/">Whole Item</a></p>'
                '</p><a href="/asset/24/">This should still be there</a></p>'
                '</p><a href="/asset/42/">This should still be there</a></p>'
                )

        old_asset = Asset.objects.get(id=2)
        new_asset = Asset.objects.get(id=1)

        new_text = new_asset.update_references_in_string(text, old_asset)

        new_asset_href = "/asset/%s/" % (new_asset.id)
        self.assertTrue(new_text.find(new_asset_href) > 0)

        old_asset_href = "/asset/24/"
        self.assertTrue(new_text.find(old_asset_href) > 0)

        citations = SherdNote.objects.references_in_string(new_text,
                                                           new_asset.author)
        self.assertEquals(len(citations), 6)
        self.assertEquals(citations[0].id, 10)
        self.assertEquals(citations[0].asset.id, 2)

        self.assertEquals(citations[1].id, 10)
        self.assertEquals(citations[1].asset.id, 2)

        self.assertEquals(citations[2].id, 8)
        self.assertEquals(citations[2].asset.id, 2)

        self.assertEquals(citations[3].id, 1)
        self.assertEquals(citations[3].asset.id, 1)

        self.assertEquals(citations[4].id, 0)
        self.assertEquals(citations[5].id, 0)

    def test_user_analysis_count(self):
        asset1 = Asset.objects.get(id=1)
        asset2 = Asset.objects.get(id=2)
        asset3 = Asset.objects.get(id=3)
        asset5 = Asset.objects.get(id=5)

        test_instructor = User.objects.get(username='test_instructor')
        self.assertEquals(asset1.user_analysis_count(test_instructor), 6)
        self.assertEquals(asset2.user_analysis_count(test_instructor), 4)
        self.assertEquals(asset3.user_analysis_count(test_instructor), 3)
        self.assertEquals(asset5.user_analysis_count(test_instructor), 0)

        test_instructor_two = User.objects.get(username='test_instructor_two')
        self.assertEquals(asset1.user_analysis_count(test_instructor_two), 3)
        self.assertEquals(asset2.user_analysis_count(test_instructor_two), 0)
        self.assertEquals(asset5.user_analysis_count(test_instructor_two), 0)

        test_student_one = User.objects.get(username='test_student_one')
        self.assertEquals(asset1.user_analysis_count(test_student_one), 0)
        self.assertEquals(asset2.user_analysis_count(test_student_one), 3)
        self.assertEquals(asset3.user_analysis_count(test_student_one), 0)

    def test_assets_by_course(self):
        course = Course.objects.get(title='Sample Course')
        user = User.objects.get(username='test_instructor')
        archive = Asset.objects.create(title="Sample Archive",
                                       course=course, author=user)
        primary = Source.objects.create(asset=archive, label='archive',
                                        primary=True,
                                        url="http://ccnmtl.columbia.edu")
        archive.source_set.add(primary)

        assets = Asset.objects.filter(course=course)
        self.assertEquals(assets.count(), 5)

        assets = Asset.objects.by_course(course=course)
        self.assertEquals(assets.count(), 4)

        # make sure the archive isn't in there
        self.assertEquals(assets.filter(title="Sample Archive").count(), 0)

    def test_assets_by_course_and_user(self):
        course = Course.objects.get(title='Sample Course')
        user = User.objects.get(username='test_instructor_two')
        archive = Asset.objects.create(title="Sample Archive",
                                       course=course, author=user)
        primary = Source.objects.create(asset=archive, label='archive',
                                        primary=True,
                                        url="http://ccnmtl.columbia.edu")
        archive.source_set.add(primary)

        # tweak project portfolio to have a non-primary archive label
        asset = Asset.objects.get(title='Project Portfolio')
        metadata = Source.objects.create(asset=asset, label='archive',
                                         primary=False,
                                         url="http://ccnmtl.columbia.edu")
        asset.source_set.add(metadata)

        assets = Asset.objects.by_course_and_user(course, user)
        self.assertEquals(assets.count(), 2)
        self.assertIsNotNone(assets.get(title='Project Portfolio'))
        self.assertIsNotNone(assets.get(title='Mediathread: Introduction'))

        # make sure the archive isn't in there
        self.assertEquals(assets.filter(title="Sample Archive").count(), 0)

        user = User.objects.get(username='test_instructor')
        assets = Asset.objects.by_course_and_user(course, user)
        self.assertEquals(assets.count(), 3)
        self.assertIsNotNone(assets.get(title='Mediathread: Introduction'))
        self.assertIsNotNone(assets.get(title='MAAP Award Reception'))
        self.assertIsNotNone(assets.get(
            title="The Armory - Home to CCNMTL'S CUMC Office"))
