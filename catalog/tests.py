from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
import re

from catalog.models import AuthAuditEvent, VerificationChallenge, VerificationProfile


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")

    def test_logout_redirects_to_archive_and_clears_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("custom_logout"), follow=True)

        self.assertRedirects(response, reverse("archive"))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("custom_logout")).status_code, 405)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_URL="http://testserver",
)
class VerificationFlowTests(TestCase):
    registration_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password1": "A-secure-password-123",
        "password2": "A-secure-password-123",
        "terms_consent": "on",
        "privacy_consent": "on",
    }

    def test_registration_requires_email_verification_before_login(self):
        response = self.client.post(reverse("register"), self.registration_data)
        self.assertRedirects(response, reverse("verification_sent"))
        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        self.assertFalse(self.client.login(username="newuser", password="A-secure-password-123"))
        profile = VerificationProfile.objects.get(user=user)
        self.assertIsNotNone(profile.terms_consent_at)
        self.assertIsNotNone(profile.privacy_consent_at)
        self.assertEqual(AuthAuditEvent.objects.get(user=user).event, "registration_created")

    def test_email_verification_is_single_use_and_activates_account(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("register"), self.registration_data)
        user = User.objects.get(username="newuser")
        message = mail.outbox[0].body
        token = re.search(r"verify-email/\d+/([^/]+)", message).group(1)
        response = self.client.get(reverse("verify_email", args=[user.pk, token]))
        self.assertRedirects(response, reverse("login") + "?verified=1")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(self.client.login(username="newuser", password="A-secure-password-123"))
        self.assertEqual(self.client.get(reverse("account_overview")).status_code, 200)
        self.assertEqual(self.client.get(reverse("verify_email", args=[user.pk, token])).status_code, 400)

    def test_phone_code_is_expiring_and_limited(self):
        user = User.objects.create_user(username="phoneuser", password="Phone-pass-123")
        self.client.force_login(user)
        response = self.client.post(reverse("start_phone_verification"), {"phone_number": "+15551234567"})
        self.assertRedirects(response, reverse("phone_verification"))
        challenge = VerificationChallenge.objects.get(user=user, channel="phone")
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save(update_fields=["expires_at"])
        response = self.client.post(reverse("phone_verification"), {"phone_number": "+15551234567", "code": "000000"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invalid or expired")
        self.assertEqual(VerificationProfile.objects.get(user=user).phone_verified_at, None)

    def test_login_preserves_protected_destination(self):
        user = User.objects.create_user(username="activeuser", password="Active-pass-123")
        response = self.client.get(reverse("my_content"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my_content')}")
        response = self.client.post(
            reverse("login"),
            {"username": "activeuser", "password": "Active-pass-123", "next": reverse("my_content")},
        )
        self.assertRedirects(response, reverse("my_content"))
