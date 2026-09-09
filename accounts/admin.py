
from django.contrib import admin
from .models import (
    Role,
    UserRole,
    Customer,
    Employee,
    CustomerAddress,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
    )

    search_fields = (
        "name",
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "role",
    )

    list_filter = (
        "role",
    )

    search_fields = (
        "user__username",
        "user__email",
        "role__name",
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "phone_number",
        "gender",
        "city",
        "state",
        "country",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "gender",
        "is_verified",
        "country",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone_number",
        "city",
        "state",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee_id",
        "user",
        "phone_number",
        "designation",
        "gender",
        "joining_date",
        "is_active",
        "created_at",
    )

    list_filter = (
        "designation",
        "gender",
        "is_active",
    )

    search_fields = (
        "employee_id",
        "user__username",
        "user__email",
        "phone_number",
        "designation",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "full_name",
        "phone_number",
        "city",
        "state",
        "country",
        "postal_code",
        "is_default",
        "created_at",
    )

    list_filter = (
        "country",
        "state",
        "is_default",
    )

    search_fields = (
        "customer__user__username",
        "customer__user__email",
        "full_name",
        "phone_number",
        "city",
        "state",
        "postal_code",
    )

    readonly_fields = (
        "created_at",
    )

