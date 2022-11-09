"""
Views for the packages API.
"""
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Package, Robot
from package import serializers


class PackageViewSet(viewsets.ModelViewSet):
    """View for manage packages APIs."""
    serializer_class = serializers.PackageSerializer
    queryset = Package.objects.all()
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'code'
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'upload_image':
            return serializers.PackageImageSerializer

        return self.serializer_class

    def perform_destroy(self, instance):
        """Destroy the package."""
        if Robot.objects.filter(packages__code=instance.code).exists():
            raise PermissionDenied(
                detail='The package is currently inside of a robot.'
            )

        return Package.delete(instance)

    def perform_create(self, serializer):
        """Create new package."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, *args, **kwargs):
        """Upload an image to package."""
        package = self.get_object()
        serializer = self.get_serializer(package, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
