import random
import secrets

from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from google.oauth2 import id_token
from google.auth.transport import requests


from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import IntegrityError
from .models import Customer, CustomerAddress
from .serializers import CustomerAddressSerializer


from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
)

from .models import (
    Customer,
    Role,
    UserRole
)


# =========================================================
# AUTH RESPONSE HELPER
# =========================================================

def _get_auth_user_data(user, request=None):
    """Return the user shape expected by the frontend auth APIs."""
    role = None
    try:
        role = user.user_role.role.name
    except (UserRole.DoesNotExist, Role.DoesNotExist, AttributeError):
        pass

    phone = None
    avatar = None
    addresses = []

    try:
        customer = user.customer
        phone = customer.phone_number

        if customer.profile_image:
            avatar = customer.profile_image.url
            if request is not None:
                avatar = request.build_absolute_uri(avatar)

        addresses = CustomerAddressSerializer(
            customer.addresses.all().order_by("-is_default", "-id"),
            many=True
        ).data
    except Customer.DoesNotExist:
        pass

    name = (f"{user.first_name} {user.last_name}").strip()
    if not name:
        name = user.username

    return {
        "id": user.id,
        "name": name,
        "email": user.email,
        "phone": phone,
        "role": role,
        "avatar": avatar,
        "addresses": addresses,
    }


# ==========================
# REGISTER API
# ==========================

class RegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        # New frontend contract:
        # {name, email, phone, password}
        if "name" in request.data:
            name = str(request.data.get("name", "")).strip()
            email = str(request.data.get("email", "")).strip().lower()
            phone = str(request.data.get("phone", "")).strip()
            password = request.data.get("password")

            if not name:
                return Response({"message": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)
            if not email:
                return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            if not phone:
                return Response({"message": "Phone is required."}, status=status.HTTP_400_BAD_REQUEST)
            if not password:
                return Response({"message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
            if len(password) < 8:
                return Response({"message": "Password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email__iexact=email).exists():
                return Response({"message": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if Customer.objects.filter(phone_number=phone).exists():
                return Response({"message": "An account with this phone number already exists."}, status=status.HTTP_400_BAD_REQUEST)

            parts = name.split(None, 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            # Keep username compatible with the existing Django authentication.
            base_username = email.split("@")[0] or "customer"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            try:
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password,
                )

                customer_role = Role.objects.get(name="Customer")
                UserRole.objects.create(user=user, role=customer_role)
                Customer.objects.create(
                    user=user,
                    phone_number=phone,
                    country="India",
                )
            except Role.DoesNotExist:
                return Response(
                    {"message": "Customer role is not configured. Create a Customer role first."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except IntegrityError:
                return Response(
                    {"message": "Unable to create the account. Email or phone may already exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Registration Successful",
                    "user": _get_auth_user_data(user, request),
                    "token": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    # Keep old keys for backward compatibility.
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "username": user.username,
                    "role": "Customer",
                },
                status=status.HTTP_201_CREATED,
            )

        # Existing registration contract — kept intact.
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = User.objects.create_user(
                    username=serializer.validated_data["username"],
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    email=serializer.validated_data["email"],
                    password=serializer.validated_data["password"]
                )

                customer_role = Role.objects.get(name="Customer")

                UserRole.objects.create(
                    user=user,
                    role=customer_role
                )

                Customer.objects.create(
                    user=user,
                    phone_number=serializer.validated_data["phone_number"],
                    gender=serializer.validated_data.get("gender"),
                    date_of_birth=serializer.validated_data.get("date_of_birth"),
                    address=serializer.validated_data.get("address"),
                    city=serializer.validated_data.get("city"),
                    state=serializer.validated_data.get("state"),
                    country=serializer.validated_data.get("country", "India"),
                    postal_code=serializer.validated_data.get("postal_code")
                )
            except Role.DoesNotExist:
                return Response(
                    {"message": "Customer role is not configured. Create a Customer role first."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except IntegrityError:
                return Response(
                    {"message": "Unable to create the account. Email, username, or phone may already exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({"message": "Registration Successful"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================
# LOGIN API
# ==========================

class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # Supports both the old username field and the new email/phone/OTP contract.
        email = str(request.data.get("email", "")).strip().lower()
        username_or_email = str(request.data.get("username", "")).strip()
        phone = str(request.data.get("phone", "")).strip()
        password = request.data.get("password")
        otp = str(request.data.get("otp", "")).strip()

        user = None

        # Phone + OTP login. OTP is created by SendLoginOTPAPIView below.
        if phone and otp and not password:
            otp_data = cache.get(f"login_otp_{phone}")

            if not otp_data:
                return Response({"message": "OTP has expired. Please request a new OTP."}, status=status.HTTP_401_UNAUTHORIZED)

            if otp_data.get("otp") != otp:
                return Response({"message": "Invalid OTP."}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                customer = Customer.objects.select_related("user").get(phone_number=phone)
                user = customer.user
            except Customer.DoesNotExist:
                return Response({"message": "No account exists with this phone number."}, status=status.HTTP_401_UNAUTHORIZED)

            cache.delete(f"login_otp_{phone}")

        else:
            login_value = email or username_or_email

            if not login_value or not password:
                return Response({"message": "Email/username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_obj = User.objects.get(email__iexact=login_value)
                username = user_obj.username
            except User.DoesNotExist:
                username = login_value

            user = authenticate(username=username, password=password)

            if user is None:
                return Response(
                    {"message": "Invalid Username/Email or Password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        refresh = RefreshToken.for_user(user)

        try:
            role = user.user_role.role.name
        except (UserRole.DoesNotExist, AttributeError):
            role = None

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "message": "Login Successful",
                "user": _get_auth_user_data(user, request),
                "token": access_token,
                "refreshToken": refresh_token,
                # Existing frontend compatibility.
                "access": access_token,
                "refresh": refresh_token,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": role,
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# SEND LOGIN OTP
# =========================================================

class SendLoginOTPAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        phone = str(request.data.get("phone", "")).strip()

        if not phone:
            return Response({"message": "Phone is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.select_related("user").get(phone_number=phone)
        except Customer.DoesNotExist:
            return Response({"message": "No account exists with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        otp = str(random.randint(100000, 999999))
        cache.set(
            f"login_otp_{phone}",
            {"otp": otp, "user_id": customer.user_id},
            timeout=300
        )

        # Your existing project has email sending configured. Without an SMS provider,
        # send the OTP to the customer's registered email instead of pretending to send SMS.
        try:
            send_mail(
                subject="PetCare Store - Login OTP",
                message=(
                    f"Hello {customer.user.first_name or customer.user.username},\n\n"
                    f"Your login OTP is: {otp}\n\n"
                    "This OTP is valid for 5 minutes.\n\n"
                    "Regards,\nPetCare Store"
                ),
                from_email=None,
                recipient_list=[customer.user.email],
                fail_silently=False,
            )
        except Exception:
            cache.delete(f"login_otp_{phone}")
            return Response(
                {"message": "Unable to send OTP."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "OTP sent successfully.", "phone": phone},
            status=status.HTTP_200_OK
        )


# =========================================================
# AUTH ME API
# =========================================================

class AuthMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_get_auth_user_data(request.user, request), status=status.HTTP_200_OK)


# =========================================================
# REFRESH TOKEN API
# =========================================================

class AuthRefreshTokenAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token") or request.data.get("refreshToken")

        if not token:
            return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(token)
            return Response({"token": str(refresh.access_token)}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"message": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)


# =========================================================
# LOGOUT API
# =========================================================

class AuthLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Blacklist the supplied refresh token when available.
        refresh_token = request.data.get("refreshToken") or request.data.get("refresh")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except (TokenError, AttributeError):
                pass

        return Response({"message": "Logout Successful"}, status=status.HTTP_200_OK)


# ==========================
# GOOGLE LOGIN API
# DO NOT TOUCH THIES CODE. THIS CODE WORKING CORRECTLY
# ==========================

class GoogleLoginAPIView(APIView):

    def post(self, request):

        token = request.data.get(
            "token"
        )


        if not token:

            return Response(
                {
                    "message":
                    "Google Token Required"
                },

                status=status.HTTP_400_BAD_REQUEST
            )


        try:


            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )


            email = idinfo.get(
                "email"
            )

            first_name = idinfo.get(
                "given_name",
                ""
            )

            last_name = idinfo.get(
                "family_name",
                ""
            )


            username = email.split("@")[0]



            user, created = User.objects.get_or_create(

                email=email,

                defaults={

                    "username":
                    username,

                    "first_name":
                    first_name,

                    "last_name":
                    last_name

                }

            )



            # Get Customer Role

            customer_role = Role.objects.get(
                name="Customer"
            )



            # Assign Role

            UserRole.objects.get_or_create(

                user=user,

                defaults={

                    "role":
                    customer_role

                }

            )



            # Create Customer Profile

            customer, created = Customer.objects.get_or_create(

                user=user,

                defaults={

                    "phone_number":
                    f"google_{user.id}",

                    "country":
                    "India"

                }

            )



            refresh = RefreshToken.for_user(
                user
            )



            return Response(

                {

                    "message":
                    "Google Login Successful",


                    "access":
                    str(refresh.access_token),


                    "refresh":
                    str(refresh),


                    "username":
                    user.username,


                    "email":
                    user.email,


                    "first_name":
                    user.first_name,


                    "last_name":
                    user.last_name,


                    "role":
                    user.user_role.role.name

                },

                status=status.HTTP_200_OK

            )


        except Exception as e:


            return Response(

                {
                    "message":
                    str(e)
                },

                status=status.HTTP_400_BAD_REQUEST

            )



# ==========================
# PROFILE API
# ==========================

class ProfileAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    def get(self, request):

        try:

            customer = Customer.objects.get(
                user=request.user
            )

            serializer = ProfileSerializer(
                customer
            )


            return Response(
                serializer.data
            )


        except Customer.DoesNotExist:


            return Response(
                {
                    "message":
                    "Customer profile not found"
                },

                status=status.HTTP_404_NOT_FOUND
            )



# ==========================
# UPDATE PROFILE API
# ==========================

class UpdateProfileAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]


    parser_classes = [
        MultiPartParser,
        FormParser
    ]



    def put(self, request):

        customer = Customer.objects.get(
            user=request.user
        )


        serializer = ProfileSerializer(
            customer,
            data=request.data,
            partial=True
        )


        if serializer.is_valid():

            serializer.save()


            return Response(
                {
                    "message":
                    "Profile updated successfully",

                    "profile":
                    serializer.data
                }
            )


        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==========================================
# ADDRESS LIST + CREATE
# ==========================================

class CustomerAddressListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    # ======================================
    # GET ALL ADDRESSES
    # ======================================

    def get(self, request):

        customer = get_object_or_404(
            Customer,
            user=request.user
        )

        addresses = (
            CustomerAddress.objects
            .filter(customer=customer)
            .order_by(
                "-is_default",
                "-id"
            )
        )

        serializer = CustomerAddressSerializer(
            addresses,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # ======================================
    # ADD NEW ADDRESS
    # ======================================

    @transaction.atomic
    def post(self, request):

        customer = get_object_or_404(
            Customer,
            user=request.user
        )

        serializer = CustomerAddressSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        requested_default = (
            request.data.get("is_default", False)
        )

        # Convert string values safely
        if isinstance(requested_default, str):
            requested_default = (
                requested_default.lower()
                in ["true", "1", "yes"]
            )

        # Check whether customer already has addresses
        has_existing_address = (
            CustomerAddress.objects
            .filter(
                customer=customer
            )
            .exists()
        )

        # ==========================================
        # FIRST ADDRESS
        # ==========================================

        if not has_existing_address:

            address = serializer.save(
                customer=customer,
                is_default=True
            )

        # ==========================================
        # NEW ADDRESS REQUESTED AS DEFAULT
        # ==========================================

        elif requested_default:

            # Remove default from previous address
            CustomerAddress.objects.filter(
                customer=customer,
                is_default=True
            ).update(
                is_default=False
            )

            # Create new default address
            address = serializer.save(
                customer=customer,
                is_default=True
            )

        # ==========================================
        # NORMAL NEW ADDRESS
        # ==========================================

        else:

            address = serializer.save(
                customer=customer,
                is_default=False
            )

        return Response(
            CustomerAddressSerializer(
                address
            ).data,
            status=status.HTTP_201_CREATED
        )


# ==========================================
# ADDRESS UPDATE + DELETE
# ==========================================

class CustomerAddressDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    # ======================================
    # GET CUSTOMER
    # ======================================

    def get_customer(self, request):

        return get_object_or_404(
            Customer,
            user=request.user
        )

    # ======================================
    # GET ADDRESS
    # ======================================

    def get_address(self, request, pk):

        customer = self.get_customer(
            request
        )

        return get_object_or_404(
            CustomerAddress,
            id=pk,
            customer=customer
        )

    # ======================================
    # UPDATE ADDRESS
    # ======================================

    @transaction.atomic
    def put(self, request, pk):

        customer = self.get_customer(
            request
        )

        address = get_object_or_404(
            CustomerAddress,
            id=pk,
            customer=customer
        )

        # ==========================================
        # CHECK WHETHER THIS ADDRESS SHOULD
        # BECOME DEFAULT
        # ==========================================

        requested_default = (
            request.data.get(
                "is_default",
                address.is_default
            )
        )

        if isinstance(requested_default, str):

            requested_default = (
                requested_default.lower()
                in ["true", "1", "yes"]
            )

        # ==========================================
        # MAKE THIS ADDRESS DEFAULT
        # ==========================================

        if requested_default:

            # Remove default from every other address
            CustomerAddress.objects.filter(
                customer=customer,
                is_default=True
            ).exclude(
                id=address.id
            ).update(
                is_default=False
            )

            # Update selected address
            serializer = CustomerAddressSerializer(
                address,
                data=request.data,
                partial=True
            )

            serializer.is_valid(
                raise_exception=True
            )

            updated_address = serializer.save(
                is_default=True
            )

        # ==========================================
        # NORMAL UPDATE
        # ==========================================

        else:

            serializer = CustomerAddressSerializer(
                address,
                data=request.data,
                partial=True
            )

            serializer.is_valid(
                raise_exception=True
            )

            updated_address = serializer.save()

        return Response(
            CustomerAddressSerializer(
                updated_address
            ).data,
            status=status.HTTP_200_OK
        )

    # ======================================
    # PATCH
    # ======================================

    @transaction.atomic
    def patch(self, request, pk):

        customer = self.get_customer(
            request
        )

        address = get_object_or_404(
            CustomerAddress,
            id=pk,
            customer=customer
        )

        requested_default = request.data.get(
            "is_default",
            None
        )

        if isinstance(requested_default, str):

            requested_default = (
                requested_default.lower()
                in ["true", "1", "yes"]
            )

        # ==========================================
        # SET DEFAULT
        # ==========================================

        if requested_default is True:

            CustomerAddress.objects.filter(
                customer=customer,
                is_default=True
            ).exclude(
                id=address.id
            ).update(
                is_default=False
            )

        serializer = CustomerAddressSerializer(
            address,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_address = serializer.save()

        return Response(
            CustomerAddressSerializer(
                updated_address
            ).data,
            status=status.HTTP_200_OK
        )

    # ======================================
    # DELETE ADDRESS
    # ======================================

    @transaction.atomic
    def delete(self, request, pk):

        customer = self.get_customer(
            request
        )

        address = get_object_or_404(
            CustomerAddress,
            id=pk,
            customer=customer
        )

        addresses = CustomerAddress.objects.filter(
            customer=customer
        )

        address_count = addresses.count()

        # ==========================================
        # DON'T ALLOW ZERO ADDRESSES
        # ==========================================

        if address_count <= 1:

            return Response(
                {
                    "success": False,
                    "message":
                        "You must have at least one address."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        was_default = address.is_default

        address.delete()

        # ==========================================
        # IF DEFAULT WAS DELETED
        # MAKE ANOTHER ADDRESS DEFAULT
        # ==========================================

        if was_default:

            new_default = (
                CustomerAddress.objects
                .filter(
                    customer=customer
                )
                .order_by("-id")
                .first()
            )

            if new_default:

                CustomerAddress.objects.filter(
                    customer=customer
                ).update(
                    is_default=False
                )

                new_default.is_default = True

                new_default.save(
                    update_fields=[
                        "is_default"
                    ]
                )

        return Response(
            {
                "success": True,
                "message":
                    "Address deleted successfully."
            },
            status=status.HTTP_200_OK
        )

class ForgotPasswordAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        # =====================================================
        # GET EMAIL
        # =====================================================

        email = request.data.get(
            "email",
            ""
        ).strip().lower()

        # =====================================================
        # CHECK EMAIL PROVIDED
        # =====================================================

        if not email:

            return Response(
                {
                    "detail": "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK USER EXISTS
        # =====================================================

        try:

            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail":
                    "No account exists with this email address."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =====================================================
        # GENERATE 6 DIGIT OTP
        # =====================================================

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        # =====================================================
        # GENERATE RESET TOKEN
        # =====================================================

        reset_token = secrets.token_urlsafe(32)

        # =====================================================
        # CACHE KEY
        # =====================================================

        cache_key = (
            f"password_reset_{reset_token}"
        )

        # =====================================================
        # STORE OTP IN CACHE
        #
        # NOT DATABASE
        #
        # 5 MINUTES
        # =====================================================

        cache.set(

            cache_key,

            {
                "user_id": user.id,

                "email": email,

                "otp": otp,

                "verified": False
            },

            timeout=300
        )

        # =====================================================

class VerifyPasswordOTPAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        # =====================================================
        # GET DATA
        # =====================================================

        email = request.data.get(
            "email",
            ""
        ).strip().lower()

        otp = request.data.get(
            "otp",
            ""
        ).strip()

        reset_token = request.data.get(
            "reset_token",
            ""
        ).strip()

        # =====================================================
        # VALIDATE EMAIL
        # =====================================================

        if not email:

            return Response(
                {
                    "detail":
                    "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # VALIDATE OTP
        # =====================================================

        if not otp:

            return Response(
                {
                    "detail":
                    "OTP is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # VALIDATE RESET TOKEN
        # =====================================================

        if not reset_token:

            return Response(
                {
                    "detail":
                    "Reset token is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # GET CACHE DATA
        # =====================================================

        cache_key = (
            f"password_reset_{reset_token}"
        )

        reset_data = cache.get(
            cache_key
        )

        # =====================================================
        # CHECK TOKEN / OTP EXPIRY
        # =====================================================

        if not reset_data:

            return Response(
                {
                    "detail":
                    "OTP has expired. Please request a new OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK EMAIL
        # =====================================================

        if reset_data.get("email") != email:

            return Response(
                {
                    "detail":
                    "Invalid password reset request."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK OTP
        # =====================================================

        if reset_data.get("otp") != otp:

            return Response(
                {
                    "detail":
                    "Invalid OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # MARK OTP VERIFIED
        # =====================================================

        reset_data["verified"] = True

        cache.set(

            cache_key,

            reset_data,

            timeout=300
        )

        # =====================================================
        # SUCCESS
        # =====================================================

        return Response(
            {
                "message":
                "OTP verified successfully.",

                "verified":
                True,

                "reset_token":
                reset_token
            },
            status=status.HTTP_200_OK
        )

# =========================================================
# RESET PASSWORD
# =========================================================

class ResetPasswordAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        # =====================================================
        # GET DATA
        # =====================================================

        email = request.data.get(
            "email",
            ""
        ).strip().lower()

        reset_token = request.data.get(
            "reset_token",
            ""
        ).strip()

        new_password = request.data.get(
            "new_password",
            ""
        )

        # =====================================================
        # CHECK EMAIL
        # =====================================================

        if not email:

            return Response(
                {
                    "detail":
                    "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK RESET TOKEN
        # =====================================================

        if not reset_token:

            return Response(
                {
                    "detail":
                    "Reset token is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK PASSWORD
        # =====================================================

        if not new_password:

            return Response(
                {
                    "detail":
                    "New password is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # PASSWORD LENGTH
        # =====================================================

        if len(new_password) < 8:

            return Response(
                {
                    "detail":
                    "Password must be at least 8 characters."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # GET RESET DATA FROM CACHE
        # =====================================================

        cache_key = (
            f"password_reset_{reset_token}"
        )

        reset_data = cache.get(
            cache_key
        )

        # =====================================================
        # TOKEN EXPIRED
        # =====================================================

        if not reset_data:

            return Response(
                {
                    "detail":
                    "Reset session has expired. Please request a new OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK EMAIL
        # =====================================================

        if reset_data.get("email") != email:

            return Response(
                {
                    "detail":
                    "Invalid password reset request."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # CHECK OTP VERIFIED
        # =====================================================

        if not reset_data.get(
            "verified",
            False
        ):

            return Response(
                {
                    "detail":
                    "Please verify the OTP first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =====================================================
        # GET USER
        # =====================================================

        try:

            user = User.objects.get(
                id=reset_data["user_id"]
            )

        except User.DoesNotExist:

            return Response(
                {
                    "detail":
                    "User account not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =====================================================
        # CHANGE PASSWORD
        # =====================================================

        user.set_password(
            new_password
        )

        user.save(
            update_fields=[
                "password"
            ]
        )

        # =====================================================
        # DELETE CACHE
        #
        # TOKEN CANNOT BE USED AGAIN
        # =====================================================

        cache.delete(
            cache_key
        )

        # =====================================================
        # SUCCESS
        # =====================================================

        return Response(
            {
                "message":
                "Password reset successfully."
            },
            status=status.HTTP_200_OK
        )