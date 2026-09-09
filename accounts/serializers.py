from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Customer, CustomerAddress


class RegisterSerializer(serializers.ModelSerializer):

    phone_number = serializers.CharField()
    gender = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False)
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "phone_number",
            "gender",
            "date_of_birth",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
        ]

    def validate(self, data):

        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "Username already exists."}
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "Email already exists."}
            )

        if Customer.objects.filter(phone_number=data["phone_number"]).exists():
            raise serializers.ValidationError(
                {"phone_number": "Phone number already exists."}
            )

        return data



class ProfileSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(
        source="user.first_name"
    )

    last_name = serializers.CharField(
        source="user.last_name"
    )

    username = serializers.CharField(
        source="user.username"
    )

    email = serializers.EmailField(
        source="user.email"
    )

    class Meta:

        model = Customer

        fields = [

            "first_name",

            "last_name",

            "username",

            "email",

            "phone_number",

            "gender",

            "date_of_birth",

            "address",

            "city",

            "state",

            "country",

            "postal_code",

            "profile_image",

        ]

    def update(self, instance, validated_data):

        user_data = validated_data.pop("user", {})

        user = instance.user

        user.first_name = user_data.get(
            "first_name",
            user.first_name
        )

        user.last_name = user_data.get(
            "last_name",
            user.last_name
        )

        user.username = user_data.get(
            "username",
            user.username
        )

        user.email = user_data.get(
            "email",
            user.email
        )

        user.save()

        for attr, value in validated_data.items():

            setattr(instance, attr, value)

        instance.save()

        return instance


class CustomerAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerAddress
        fields = "__all__"
        read_only_fields = ["customer"]

