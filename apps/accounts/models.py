from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Телефон обязателен")
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone = PhoneNumberField(unique=True, verbose_name="Телефон")
    name = models.CharField("Имя", max_length=150, blank=True)
    email = models.EmailField("Email", blank=True)

    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Сотрудник", default=False)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
    verbose_name = "Пользователь"

    objects = UserManager()

    def __str__(self):
        return str(self.phone)


class PhoneOTP(models.Model):
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.phone} — {self.code}"

    def is_valid(self):
        return (
            not self.is_used
            and timezone.now() < self.expires_at
            and self.attempts < 5
        )
