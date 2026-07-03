from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from common.models import SoftDeleteQuerySet


class CustomUserManager(UserManager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllUsersManager(UserManager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


def avatar_upload_to(instance, filename):
    return f"avatars/{instance.pk or 'new'}/{filename}"


class User(AbstractUser):
    email = models.EmailField("email address", unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()
    all_objects = AllUsersManager()

    def save(self, *args, **kwargs):
        self.email = self.email or None
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["is_deleted", "is_active", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return self.full_name or self.username
