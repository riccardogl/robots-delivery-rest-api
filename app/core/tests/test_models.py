"""
Tests for models.
"""
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='user@example.com', password='12345678'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


def create_package(user, code, name='Testing', weight='200'):
    """Create and return a new package."""
    return models.Package.objects.create(
        user=user,
        code=code,
        name=name,
        weight=weight
    )


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = '12345678'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, '12345678')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', '12345678')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            '12345678',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_robot(self):
        """Test creating a robot is successful."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            '12345678'
        )
        robot = models.Robot.objects.create(
            user=user,
            serial_number='23def9',
            robot_model=1,
            weight_limit=400,
        )

        self.assertEqual(robot.serial_number, str(robot))

    def test_create_package(self):
        """Test creating a package is successful."""

        user = create_user()
        package = create_package(user, 'TESTING_1')

        self.assertEqual(str(package), package.name)

    @patch('core.models.uuid.uuid4')
    def test_package_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.package_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/packages/{uuid}.jpg')
