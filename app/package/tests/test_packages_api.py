"""
Tests for the packages API.
"""
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


from rest_framework import status
from rest_framework.test import APIClient

from core.models import Package, Robot

from package.serializers import PackageSerializer


PACKAGES_URL = reverse('package:package-list')


def create_package(user, code, name='Testing', weight='200'):
    """Create and return a new package."""
    return Package.objects.create(
        user=user,
        code=code,
        name=name,
        weight=weight
    )


def image_upload_url(package_url):
    """Create and return an image upload URL."""
    return reverse('package:package-upload-image', args=[package_url])


def create_robot(user, serial_number, **params):
    """Create and return a sample robot."""
    robot = Robot.objects.create(
        user=user,
        serial_number=serial_number,
        **params
    )
    return robot


def detail_url(package_code):
    """Create and return a package detail URL."""
    return reverse('package:package-detail', args=[package_code])


def create_user(email='user@example.com', password='12345678'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicPackagesApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving packages."""
        res = self.client.get(PACKAGES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePackagesApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_packages(self):
        """Test retrieving a list of packages."""
        create_package(user=self.user, code='TESTING1')
        create_package(user=self.user, code='TESTING2')

        res = self.client.get(PACKAGES_URL)

        packages = Package.objects.all().order_by('-name')
        serializer = PackageSerializer(packages, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_packages_limited_to_user(self):
        """Test list of packages is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        create_package(user=user2, code='TESTING1')
        package = create_package(user=self.user, code='TESTING2')

        res = self.client.get(PACKAGES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['code'], package.code)
        self.assertEqual(res.data[0]['name'], package.name)

    