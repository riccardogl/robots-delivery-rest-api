"""
Serializers for robot APIs
"""
from rest_framework import serializers

from core.models import Robot, Package
from rest_framework.exceptions import ParseError

from package.serializers import PackageSerializer


class ChoicesField(serializers.ChoiceField):
    """Custom ChoiceField serializer field."""

    def __init__(self, choices, **kwargs):
        """init."""
        self._choices = choices
        super(ChoicesField, self).__init__(choices, **kwargs)

    def to_representation(self, obj):
        """Used while retrieving value for the field."""
        return self._choices[obj]

    def to_internal_value(self, data):
        """Used while storing value for the field."""
        for i in range(len(self._choices)):
            try:
                if i == int(data):
                    return i
            except ValueError:
                if str(self._choices[i]) == data:
                    return i

        raise serializers.ValidationError(
            f'Acceptable values are {dict(self._choices)}.'
        )


class RobotSerializer(serializers.ModelSerializer):
    """Serializer for Robots."""
    robot_model = ChoicesField(Robot.ROBOT_MODEL)
    state = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Robot
        lookup_field = 'serial_number'
        fields = [
            'serial_number',
            'robot_model',
            'battery',
            'state',
            'weight_limit',
            'packages'
            ]
        read_only_fields = [
            'battery',
            'state',
            'weight_limit',
            'packages',
            ]


class RobotDetailSerializer(RobotSerializer):
    """Serializer for robot detail view."""
    packages = PackageSerializer(many=True, read_only=True)

    class Meta(RobotSerializer.Meta):
        fields = RobotSerializer.Meta.fields + [
            'packages',
            ]


class RobotPackagesSerializer(serializers.ModelSerializer):
    """Serializer for packages detail view."""
    packages = PackageSerializer(many=True, read_only=True)

    class Meta():
        model = Robot
        lookup_field = 'serial_number'
        fields = [
            'packages',
            ]
        read_only_fields = [
            'packages',
            ]


class RobotBatterySerializer(serializers.ModelSerializer):
    """Serializer for packages detail view."""

    class Meta():
        model = Robot
        lookup_field = 'serial_number'
        fields = [
            'battery'
            ]
        read_only_fields = [
            'battery',
            ]


class RobotAddSerializer(serializers.ModelSerializer):
    """Serializer for add package to robot."""
    class Meta:
        model = Robot
        lookup_field = 'serial_number'
        fields = [
            'serial_number',
            'weight_limit',
            'packages',
            ]
        read_only_fields = [
            'weight_limit',
            'serial_number',
            ]

    def update(self, instance, validated_data):
        """Add package to robot."""
        if instance.state == Robot.ROBOT_STATUS.idl or \
                instance.state == Robot.ROBOT_STATUS.ldg:

            packages = validated_data.pop('packages', None)

            if len(set(packages)) != len(packages):
                raise ParseError(detail='You cannot load the same '
                                        'package twice into a robot.')

            if packages is not None and len(packages) > 0:
                insert_packages = []
                auth_user = self.context['request'].user
                user_meds = packages.objects.filter(user=auth_user)
                robot_remianing_space = instance.weight_limit

                for item in packages:
                    if instance.packages.filter(code=item).exists():
                        raise ParseError(detail=f'The package {item} '
                                                'is already loaded into this'
                                                ' robot. You cannot load the'
                                                ' same package twice into'
                                                ' a robot.')

                for item in packages:
                    try:
                        new_package = Package.objects.get(
                                user=auth_user,
                                code=item
                                )
                        robot_remianing_space -= new_package.weight
                        if robot_remianing_space < 0:
                            raise ParseError(detail='The robot cannot load '
                                                    'the total weight of the'
                                                    ' selected packages.')

                        insert_packages.append(new_package)
                    except Package.DoesNotExist:
                        if len(user_meds):
                            detail = 'The available packages are '\
                                    f'{[m.code for m in user_meds]}.'
                            raise ParseError(detail=detail)
                        else:
                            raise ParseError(detail='You have to '
                                                    'create a package '
                                                    'first.')

                for pckg_get in insert_packages:
                    instance.packages.add(pckg_get)
                    instance.weight_limit -= pckg_get.weight
        else:
            raise ParseError(detail='The robot can only be loaded on '
                                    'Idle and Loading states.')

        instance.save()
        return instance
