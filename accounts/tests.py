from django.test import TestCase
from django.utils import timezone

from .models import Account, UserProfile


class AccountProfileSignalTests(TestCase):
    def test_fixture_account_save_does_not_create_duplicate_profile(self):
        account = Account(
            first_name='Fixture',
            last_name='Owner',
            username='fixture-owner',
            email='fixture-owner@example.com',
            password='encoded-password',
            date_joined=timezone.now(),
            last_login=timezone.now(),
        )

        account.save_base(raw=True)

        self.assertFalse(UserProfile.objects.filter(user=account).exists())
        profile = UserProfile.objects.create(user=account)
        self.assertEqual(profile.user, account)

    def test_regular_account_save_creates_profile(self):
        account = Account.objects.create_user(
            first_name='Shop',
            last_name='Owner',
            username='shop-owner',
            email='shop-owner@example.com',
            password='test-password-123',
        )

        self.assertTrue(UserProfile.objects.filter(user=account).exists())
