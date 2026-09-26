from django.conf import settings
from django.db import models
from django.utils import timezone


class AudioFile(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    publish_date = models.DateField()
    image = models.ImageField(upload_to="audio_images/")
    audio_file = models.FileField(upload_to="audio_files/")

    class Meta:
        indexes = [
            models.Index(fields=["category"], name="audio_category_idx"),
            models.Index(fields=["publish_date"], name="audio_publish_date_idx"),
            models.Index(fields=["price"], name="audio_price_idx"),
            models.Index(fields=["category", "publish_date"], name="audio_category_date_idx"),
            models.Index(fields=["name"], name="audio_name_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name="audio_price_nonnegative"),
        ]

    def __str__(self):
        return self.name


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    audio_file = models.ForeignKey(AudioFile, on_delete=models.CASCADE, related_name="purchases")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="RUB")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=32, default="demo")
    provider_reference = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "audio_file"], name="purchase_user_audio_unique"),
        ]
        indexes = [
            models.Index(fields=["user", "created_at"], name="purchase_user_created_idx"),
            models.Index(fields=["user", "status", "created_at"], name="purchase_user_status_idx"),
        ]

    def __str__(self):
        return f"{self.user.username} purchased {self.audio_file.name} [{self.status}]"


class VerificationProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_profile")
    phone_number = models.CharField(max_length=32, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    terms_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_consent_at = models.DateTimeField(null=True, blank=True)
    consent_version = models.CharField(max_length=32, blank=True)

    @property
    def email_verified(self):
        return self.email_verified_at is not None

    @property
    def phone_verified(self):
        return self.phone_verified_at is not None


class VerificationChallenge(models.Model):
    CHANNEL_EMAIL = "email"
    CHANNEL_PHONE = "phone"
    CHANNEL_CHOICES = [(CHANNEL_EMAIL, "Email"), (CHANNEL_PHONE, "Phone")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_challenges")
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    token_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "channel", "expires_at"], name="challenge_lookup_idx"),
            models.Index(fields=["expires_at"], name="challenge_expiry_idx"),
        ]

    @property
    def usable(self):
        return self.consumed_at is None and self.expires_at > timezone.now()


class AuthAuditEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"], name="auth_audit_user_created_idx")]
