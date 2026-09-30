from django.db import models
from django.utils import timezone


class PhoneOTP(models.Model):
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_valid(self):
        return (
            not self.is_used
            and timezone.now() < self.expires_at
            and self.attempts < 5
        )

    def __str__(self):
        return f"{self.phone} — {self.code}"