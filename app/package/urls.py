"""
URL mappings for the robot app.
"""
from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter

from package import views


router = DefaultRouter()
router.register('package', views.PackageViewSet)

app_name = 'package'

urlpatterns = [
    path('', include(router.urls)),
]
