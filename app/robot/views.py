"""
Views for the robot API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q
from core.models import Robot
from robot import serializers


class RobotViewSet(viewsets.ModelViewSet):
    """View for manage robot APIs."""

    serializer_class = serializers.RobotDetailSerializer
    queryset = Robot.objects.all()
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'serial_number'
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve robots for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by(
            'serial_number'
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RobotSerializer
        elif self.action == 'load_package':
            return serializers.RobotAddSerializer
        elif self.action == 'check_package':
            return serializers.RobotPackagesSerializer
        elif self.action == 'check_battery':
            return serializers.RobotBatterySerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create new robot."""
        serializer.save(user=self.request.user)

    @action(detail=False, serializer_class=serializers.RobotSerializer)
    def check_available(self, *args, **kwargs):
        """List all available robot to load packages."""

        available_robots = Robot.objects.filter(Q(state=0) | Q(state=1))
        serializer = serializers.RobotSerializer(available_robots, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def load_package(self, request, *args, **kwargs):
        """Loads the package into the selected robot."""
        obj = self.get_object()
        return self.get_and_return_response(request, obj, True)

    @action(detail=True)
    def check_package(self, request, *args, **kwargs):
        """Return the packages loaded into the selected robot."""
        obj = self.get_object()
        return self.get_and_return_response(request, obj)

    @action(detail=True)
    def check_battery(self, request, *args, **kwargs):
        """Check the battery of the robot."""
        obj = self.get_object()
        return self.get_and_return_response(request, obj)

    def get_and_return_response(self, request, obj, update=False):
        serializer = self.get_serializer(obj, data=request.data)

        if serializer.is_valid():
            if update:
                serializer.update(obj, request.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
