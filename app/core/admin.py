"""
Django admin customization.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )


class PackageAdmin(admin.ModelAdmin):
    ordering = ['code']
    list_display = ['code', 'name', 'weight']
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(PackageAdmin, self).get_readonly_fields(
            request,
            obj
            )

        if obj:
            return readonly_fields + ['code', 'weight']
        return readonly_fields


class RobotAdmin(admin.ModelAdmin):
    ordering = ['serial_number']
    list_display = [
        'serial_number',
        'robot_model',
        'weight_limit',
        'battery',
        'state']
    readonly_fields = ['battery', 'state', 'weight_limit', 'packages']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(RobotAdmin, self).get_readonly_fields(
            request,
            obj
            )

        if obj:
            return readonly_fields + ['robot_model']
        return readonly_fields


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Robot, RobotAdmin)
admin.site.register(models.Package, PackageAdmin)
