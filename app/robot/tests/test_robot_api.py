"""
Tests for robot APIs.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Robot, Package

from robot.serializers import (
    RobotSerializer,
    RobotDetailSerializer,
    )


ROBOTS_URL = reverse('robot:robot-list')


def detail_url(robot_sn):
    """Create and return a robot detail URL."""
    return reverse('robot:robot-detail', args=[robot_sn])


def add_package_url(robot_sn):
    """Create and return a robot load-package URL."""
    return reverse('robot:robot-load-package', args=[robot_sn])


def create_robot(user, serial_number, **params):
    """Create and return a sample robot."""
    robot = Robot.objects.create(
        user=user,
        serial_number=serial_number,
        **params
    )
    return robot


def create_package(user, code, name='Testing', weight='200'):
    """Create and return a new package."""
    return Package.objects.create(
        user=user,
        code=code,
        name=name,
        weight=weight
    )


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRobotAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(ROBOTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRobotAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com', password='12345678')
        self.client.force_authenticate(self.user)

    def test_retrieve_robots(self):
        """Test retrieving a list of robots"""

        create_robot(user=self.user, serial_number="test1")
        create_robot(user=self.user, serial_number="test2")

        res = self.client.get(ROBOTS_URL)

        robots = Robot.objects.all().order_by('serial_number')
        serializer = RobotSerializer(robots, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_robot_list_limited_to_user(self):
        """Test list of robots is limited to authenticated user."""

        other_user = create_user(
            email='test2@example.com',
            password='12345678'
        )
        create_robot(user=other_user, serial_number='Test1')
        create_robot(user=self.user, serial_number='Test2')

        res = self.client.get(ROBOTS_URL)

        robots = Robot.objects.filter(user=self.user)
        serializer = RobotSerializer(robots, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_robot_detail(self):
        """Test get robot detail."""
        robot = create_robot(user=self.user, serial_number='Test1')

        url = detail_url(robot.serial_number)
        res = self.client.get(url)

        serializer = RobotDetailSerializer(robot)
        self.assertEqual(res.data, serializer.data)

    def test_create_robot(self):
        """Test creating a robot."""
        payload = {
            'serial_number': 'Test1',
            'robot_model': 2,
        }
        res = self.client.post(ROBOTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        robot = Robot.objects.get(serial_number=res.data['serial_number'])
        for k, v in payload.items():
            self.assertEqual(getattr(robot, k), v)
        self.assertEqual(robot.user, self.user)

    def test_cannot_update(self):
        """Test that put and patch enpoints are disabled."""
        robot = create_robot(user=self.user, serial_number='Test1')
        url = detail_url(robot.serial_number)

        payload = {'serial_number': 'test23'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_create_incorrect_sn(self):
        """Test cannot create robot with incorrect serial number."""

        payload = {'serial_number': 'tst'}
        res = self.client.post(ROBOTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Robot.objects.filter(serial_number='tst').exists())

    def test_delete_robot(self):
        """Test deleting a robot successful."""
        robot = create_robot(user=self.user, serial_number='Test1')

        url = detail_url(robot.serial_number)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Robot.objects.filter(serial_number=robot.serial_number).exists()
        )

    def test_delete_other_user_robot_error(self):
        """Test trying to delete another users robot gives error."""

        other_user = create_user(
            email='test2@example.com',
            password='12345678'
        )
        robot = create_robot(user=other_user, serial_number='Test1')

        url = detail_url(robot.serial_number)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Robot.objects.filter(serial_number=robot.serial_number).exists()
        )

    def test_add_package_robot(self):
        """Test add a package to selected robot."""
        robot = create_robot(
            user=self.user,
            serial_number='Test1',
            robot_model=3)

        package = create_package(user=self.user, code='TEST1')
        package2 = create_package(user=self.user, code='TEST2')

        payload = {'packages': ['TEST1', 'TEST2']}
        url = add_package_url(robot.serial_number)
        res = self.client.post(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(package2, robot.packages.all())
        self.assertIn(package, robot.packages.all())

    def test_add_duplicate_packages_robot(self):
        """Test error when trying to add the same package."""
        robot = create_robot(user=self.user, serial_number='Test1')
        package = create_package(user=self.user, code='TEST1')

        payload = {'packages': ['TEST1', 'TEST1']}
        url = add_package_url(robot.serial_number)
        res = self.client.post(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(package, robot.packages.all())

    def test_add_package_overweight_robot(self):
        """Test add a package overweight to selected robot."""
        robot = create_robot(
            user=self.user,
            serial_number='Test1'
            )

        package = create_package(
            user=self.user,
            code='TEST1',
            weight=400
            )

        package2 = create_package(
            user=self.user,
            code='TEST2'
            )

        payload = {'packages': ['TEST1', 'TEST2']}
        url = add_package_url(robot.serial_number)
        res = self.client.post(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(package2, robot.packages.all())
        self.assertNotIn(package, robot.packages.all())

    def test_add_package_moving_robot(self):
        """Test add a package to a robot that is moving."""
        robot = create_robot(
            user=self.user,
            serial_number='Test1',
            state=Robot.ROBOT_STATUS.ret,
            )

        package = create_package(
            user=self.user,
            code='TEST1',
            weight=100
            )

        payload = {'packages': ['TEST1']}
        url = add_package_url(robot.serial_number)
        res = self.client.post(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(package, robot.packages.all())