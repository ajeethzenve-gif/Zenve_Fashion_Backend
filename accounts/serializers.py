from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Customer,
    CustomerAddress,
    Role,
    UserRole,
)


# ============================================================
# USER SERIALIZER
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "role",
            "avatar",
            "addresses",
        ]

    def get_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()

        if full_name:
            return full_name

        return obj.username

    def get_phone(self, obj):
        try:
            return obj.customer.phone_number
        except Customer.DoesNotExist:
            return None

    def get_role(self, obj):
        try:
            return obj.user_role.role.name
        except UserRole.DoesNotExist:
            return None

    def get_avatar(self, obj):
        try:
            profile_image = obj.customer.profile_image

            if profile_image:
                request = self.context.get("request")

                if request:
                    return request.build_absolute_uri(
                        profile_image.url
                    )

                return profile_image.url

        except Customer.DoesNotExist:
            pass

        return None

    def get_addresses(self, obj):
        try:
            addresses = obj.customer.addresses.all().order_by(
                "-is_default",
                "-id",
            )

            return CustomerAddressSerializer(
                addresses,
                many=True,
                context=self.context,
            ).data

        except Customer.DoesNotExist:
            return []


# ============================================================
# REGISTER SERIALIZER
# ============================================================

class RegisterSerializer(serializers.Serializer):
    """
    Supports the new frontend registration payload:

    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "9876543210",
        "password": "password123"
    }

    Also keeps compatibility with the previous registration
    fields used by the existing backend.
    """

    # New fields
    name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=15,
    )

    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        min_length=8,
    )

    # Existing/legacy fields
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=15,
    )

    gender = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    city = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    state = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    country = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    postal_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def validate_email(self, value):
        value = value.strip().lower()

        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if value and Customer.objects.filter(
            phone_number=value
        ).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )

        return value

    def validate_phone_number(self, value):
        value = value.strip()

        if value and Customer.objects.filter(
            phone_number=value
        ).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )

        return value

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        return value

    def validate(self, attrs):
        """
        Normalize new frontend fields into the fields expected
        by the existing RegisterAPIView.
        """

        # ----------------------------------------------------
        # Name → first_name / last_name
        # ----------------------------------------------------

        name = attrs.get("name", "").strip()

        if name:
            name_parts = name.split()

            attrs["first_name"] = name_parts[0]

            if len(name_parts) > 1:
                attrs["last_name"] = " ".join(name_parts[1:])
            else:
                attrs["last_name"] = ""

        # ----------------------------------------------------
        # phone → phone_number
        # ----------------------------------------------------

        phone = attrs.get("phone", "").strip()

        if phone:
            attrs["phone_number"] = phone

        # ----------------------------------------------------
        # Required email
        # ----------------------------------------------------

        email = attrs.get("email", "").strip().lower()

        if not email:
            raise serializers.ValidationError(
                {
                    "email": "Email is required."
                }
            )

        attrs["email"] = email

        # ----------------------------------------------------
        # Required phone
        # ----------------------------------------------------

        phone_number = (
            attrs.get("phone_number")
            or attrs.get("phone")
            or ""
        ).strip()

        if not phone_number:
            raise serializers.ValidationError(
                {
                    "phone": "Phone number is required."
                }
            )

        attrs["phone_number"] = phone_number

        # ----------------------------------------------------
        # Password
        # ----------------------------------------------------

        password = attrs.get("password", "")

        if not password:
            raise serializers.ValidationError(
                {
                    "password": "Password is required."
                }
            )

        if len(password) < 8:
            raise serializers.ValidationError(
                {
                    "password": "Password must be at least 8 characters long."
                }
            )

        # ----------------------------------------------------
        # Username
        #
        # New frontend does not send username.
        # The view can generate it from email.
        # ----------------------------------------------------

        if not attrs.get("username"):
            username_base = email.split("@")[0]

            username_base = "".join(
                character
                for character in username_base
                if character.isalnum() or character in "._-"
            )

            attrs["username"] = username_base or "user"

        return attrs


# ============================================================
# CUSTOMER PROFILE SERIALIZER
# ============================================================

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    first_name = serializers.CharField(
        source="user.first_name",
        required=False,
    )

    last_name = serializers.CharField(
        source="user.last_name",
        required=False,
    )

    name = serializers.SerializerMethodField(
        read_only=True,
    )

    phone = serializers.CharField(
        source="phone_number",
        required=False,
    )

    role = serializers.SerializerMethodField(
        read_only=True,
    )

    avatar = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta:
        model = Customer
        fields = [
            "id",
            "username",
            "name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "phone_number",
            "gender",
            "date_of_birth",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "profile_image",
            "avatar",
            "is_verified",
            "role",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "name",
            "avatar",
            "role",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def get_name(self, obj):
        full_name = (
            f"{obj.user.first_name} {obj.user.last_name}"
        ).strip()

        if full_name:
            return full_name

        return obj.user.username

    def get_role(self, obj):
        try:
            return obj.user.user_role.role.name
        except UserRole.DoesNotExist:
            return None

    def get_avatar(self, obj):
        if not obj.profile_image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.profile_image.url
            )

        return obj.profile_image.url

    def update(self, instance, validated_data):
        """
        Update both Customer fields and User fields.
        """

        user = instance.user

        # ----------------------------------------------------
        # User fields
        # ----------------------------------------------------

        first_name = validated_data.pop(
            "user",
            {}
        ).get("first_name")

        last_name = None

        # Because nested source fields can be represented
        # differently by DRF, safely handle them below.
        if first_name is not None:
            user.first_name = first_name

        if "last_name" in validated_data:
            last_name = validated_data.pop("last_name")

        # ----------------------------------------------------
        # Customer fields
        # ----------------------------------------------------

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        user.save()

        return instance


# ============================================================
# CUSTOMER ADDRESS SERIALIZER
# ============================================================

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress

        fields = [
            "id",
            "full_name",
            "phone_number",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "postal_code",
            "is_default",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_phone_number(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Phone number is required."
            )

        return value

    def validate(self, attrs):
        """
        Prevent an invalid empty address.
        """

        required_fields = [
            "full_name",
            "phone_number",
            "address_line1",
            "city",
            "state",
            "country",
            "postal_code",
        ]

        for field in required_fields:
            value = attrs.get(field)

            if value is None or (
                isinstance(value, str)
                and not value.strip()
            ):
                raise serializers.ValidationError(
                    {
                        field: f"{field.replace('_', ' ').title()} is required."
                    }
                )

        return attrs


# ============================================================
# ROLE SERIALIZER
# ============================================================

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
        ]


# ============================================================
# USER ROLE SERIALIZER
# ============================================================

class UserRoleSerializer(serializers.ModelSerializer):
    user = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    role = serializers.CharField(
        source="role.name",
        read_only=True,
    )

    class Meta:
        model = UserRole
        fields = [
            "id",
            "user",
            "role",
        ]