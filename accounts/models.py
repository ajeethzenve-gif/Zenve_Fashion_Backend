from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):

    name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class UserRole(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="user_role"
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_roles"
    )

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class Customer(models.Model):

    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer"
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to="customers/",
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.user.username


class Employee(models.Model):

    DESIGNATION_CHOICES = (
        ("Admin", "Admin"),
        ("Merchandiser", "Merchandiser"),
        ("Catalogue QA", "Catalogue QA"),
        ("Operations", "Operations"),
        ("Finance", "Finance"),
        ("Designer", "Designer"),
        ("Other", "Other"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employee"
    )

    employee_id = models.CharField(
        max_length=50,
        unique=True
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )

    designation = models.CharField(
        max_length=50,
        choices=DESIGNATION_CHOICES
    )

    gender = models.CharField(
        max_length=10,
        choices=Customer.GENDER_CHOICES,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default="India"
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to="employees/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    joining_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.employee_id} - {self.user.username} - {self.designation}"


class CustomerAddress(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    full_name = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=15
    )

    address_line1 = models.CharField(
        max_length=255
    )

    address_line2 = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    country = models.CharField(
        max_length=100
    )

    postal_code = models.CharField(
        max_length=10
    )

    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.full_name