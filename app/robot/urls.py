"""
URL mappings for the robot app.
"""
from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter

from robot import views


router = DefaultRouter()
router.register('robot', views.RobotViewSet)

app_name = 'robot'

urlpatterns = [
    path('', include(router.urls)),
]
