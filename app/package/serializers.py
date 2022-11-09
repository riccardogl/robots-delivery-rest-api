"""
Serializers for package APIs
"""
from rest_framework import serializers

from core.models import Package


class PackageSerializer(serializers.ModelSerializer):
    """Serializer for packages."""

    class Meta:
        model = Package
        lookup_field = 'code'
        fields = [
            'code',
            'name',
            'weight',
            'image'
            ]
        read_only_fields = [
        ]


class PackageImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipe."""

    class Meta:
        model = Package
        fields = ['code', 'image']
        read_only_fields = ['code']
        extra_kwargs = {'image': {'required': 'True'}}
