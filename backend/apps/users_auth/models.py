from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user. Roles are modeled via Django Groups (Super Admin, Accountant, ...)."""

    class Language(models.TextChoices):
        EN = "en", "English"
        AR = "ar", "العربية"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    preferred_language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.EN
    )
    is_active = models.BooleanField(default=True)

    REQUIRED_FIELDS = ["email"]

    def role_names(self):
        return list(self.groups.values_list("name", flat=True))

    def __str__(self):
        return self.username
