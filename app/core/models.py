"""
Database models.
"""
import uuid
import os

from model_utils import Choices
from django.conf import settings
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    MinLengthValidator,
    RegexValidator,
)
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def package_image_file_path(instance, filename):
    """Generate file path for new package image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'package', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Robot(models.Model):
    """Robot object."""

    ROBOT_MODEL = Choices(
        (0, 'lw', _('Lightweight')),
        (1, 'mw', _('Middleweight')),
        (2, 'cw', _('Cruiserweight')),
        (3, 'hw', _('Heavyweight')),
    )

    ROBOT_WEIGHTS = [
        100,
        250,
        350,
        500
    ]

    ROBOT_STATUS = Choices(
        (0, 'idl', _('Idle')),
        (1, 'ldg', _('Loading')),
        (2, 'ldd', _('Loaded')),
        (3, 'dlg', _('Delivering')),
        (4, 'dld', _('Delivered')),
        (5, 'ret', _('Returning')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    serial_number = models.CharField(
        primary_key=True,
        max_length=100,
        unique=True,
        validators=[
            MinLengthValidator(5)
        ]
        )

    robot_model = models.IntegerField(
        default=ROBOT_MODEL.lw,
        choices=ROBOT_MODEL,
        )

    weight_limit = models.IntegerField(
        validators=[
            MaxValueValidator(500),
            MinValueValidator(1)
        ]
        )

    battery = models.IntegerField(
        default=100,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(0)
        ],
        )

    state = models.IntegerField(
        default=ROBOT_STATUS.idl,
        choices=ROBOT_STATUS,
    )

    packages = models.ManyToManyField('Package')

    def __str__(self):
        return self.serial_number


@receiver(models.signals.pre_save, sender=Robot)
def set_default_weight_limit(sender, instance, *args, **kwargs):
    """
    Set the default value for `weight_limit` on the `instance`.
    """
    if instance.weight_limit is None:
        instance.weight_limit = instance.ROBOT_WEIGHTS[instance.robot_model]


class Package(models.Model):
    """Package that can be loaded on Robots."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    code = models.CharField(
        primary_key=True,
        max_length=50,
        unique=True,
        validators=[
            MinLengthValidator(5),
            RegexValidator(
                regex=r'\b[A-Z0-9_]+\b',
                message='Only uppercase, numbers and underscore.',
            )
        ]
        )

    name = models.CharField(
        max_length=255,
        validators=[
            MinLengthValidator(5),
            RegexValidator(
                regex=r'\b[a-zA-Z0-9_-]+\b',
                message='Only Alphanumeric, underscore and score.'
            )
        ]
    )

    weight = models.IntegerField(
        validators=[
            MaxValueValidator(500),
            MinValueValidator(1)
        ]
    )
    image = models.ImageField(null=True, upload_to=package_image_file_path)

    def __str__(self):
        return self.name


@receiver(models.signals.post_delete, sender=Package)
def post_delete_package(sender, instance, *args, **kwargs):
    """ Clean Old Image file """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
