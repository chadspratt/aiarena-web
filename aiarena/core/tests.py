import os

from django.core.files import File
from django.test import TestCase

from aiarena.core.models import User, Bot, Map
from aiarena.core.utils import calculate_md5


class BaseTestCase(TestCase):
    # For some reason using an absolute file path here will cause it to mangle the save directory and fail
    # later whilst handling the bot_zip file save
    test_bot_zip = open('./aiarena/core/test_bot.zip', 'rb')


class LoggedInTestCase(BaseTestCase):
    def setUp(self):
        self.staffUser = User.objects.create_user(username='staff_user', password='x', email='staff_user@aiarena.net',
                                                  is_staff=True)
        self.regularUser = User.objects.create_user(username='regular_user', password='x',
                                                    email='regular_user@aiarena.net')


class MatchReadyTestCase(LoggedInTestCase):
    def setUp(self):
        super(MatchReadyTestCase, self).setUp()

        self.regularUserBot1 = Bot.objects.create(user=self.regularUser, name='regularUserBot1', active=False,
                                                  bot_zip=File(self.test_bot_zip), plays_race='T', type='Python')

        self.regularUserBot2 = Bot.objects.create(user=self.regularUser, name='regularUserBot2', active=False,
                                                  bot_zip=File(self.test_bot_zip), plays_race='Z', type='Python')

        self.staffUserBot1 = Bot.objects.create(user=self.staffUser, name='staffUserBot1', active=False,
                                                bot_zip=File(self.test_bot_zip), plays_race='P', type='Python')

        self.staffUserBot2 = Bot.objects.create(user=self.staffUser, name='staffUserBot2', active=False,
                                                bot_zip=File(self.test_bot_zip), plays_race='R', type='Python')
        Map.objects.create(name='testmap')


# User this to pre-build a full dataset for testing
class FullDataSetTestCase(MatchReadyTestCase):
    def setUp(self):
        super(FullDataSetTestCase, self).setUp()
        # todo: generate some matches and results
        pass


class UtilsTestCase(BaseTestCase):
    def test_calc_md5(self):
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_bot.zip')
        file = open(filename, 'rb')
        self.assertEqual('7411028ba931baaad47bf5810215e4f8', calculate_md5(file))


class UserTestCase(BaseTestCase):
    def test_user_creation(self):
        User.objects.create(username='test user', email='test@test.com')


class BotTestCase(BaseTestCase):
    def test_bot_creation(self):
        user = User.objects.create(username='test user', email='test@test.com')
        # For some reason using an absolute file path here for will cause it to mangle the save directory and fail
        # later whilst handling the bot_zip file save
        bot = Bot.objects.create(user=user, name='test', bot_zip=File(self.test_bot_zip), plays_race='T', type='Python')
        self.assertEqual('7411028ba931baaad47bf5810215e4f8', bot.bot_zip_md5hash)


class PageRenderTestCase(FullDataSetTestCase):
    """
    Tests to ensure website pages don't break.
    """

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_bots_page(self):
        response = self.client.get('/bots/')
        self.assertEqual(response.status_code, 200)

    def test_bot_page(self):
        response = self.client.get('/bots/{0}/'.format(self.regularUserBot1.id))
        self.assertEqual(response.status_code, 200)


class PrivateStorageTestCase(MatchReadyTestCase):
    pass  # todo
