from django.urls import path

from .views import (
    # ========================================================
    # AUTH
    # ========================================================
    RegisterAPIView,
    LoginAPIView,
    GoogleLoginAPIView,
    SendLoginOTPAPIView,
    AuthMeAPIView,
    AuthRefreshTokenAPIView,
    AuthLogoutAPIView,

    # ========================================================
    # PROFILE
    # ========================================================
    ProfileAPIView,
    UpdateProfileAPIView,

    # ========================================================
    # ADDRESS
    # ========================================================
    CustomerAddressListCreateAPIView,
    CustomerAddressDetailAPIView,

    # ========================================================
    # PASSWORD RESET
    # ========================================================
    ForgotPasswordAPIView,
    VerifyPasswordOTPAPIView,
    ResetPasswordAPIView,
)


urlpatterns = [

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    # New frontend-compatible registration
    path(
        "auth/register/",
        RegisterAPIView.as_view(),
        name="auth-register",
    ),

    # Email/password or phone/OTP login
    path(
        "auth/login/",
        LoginAPIView.as_view(),
        name="auth-login",
    ),

    # Send OTP for phone login
    path(
        "auth/send-otp/",
        SendLoginOTPAPIView.as_view(),
        name="auth-send-otp",
    ),

    # Google Login
    path(
        "auth/google/",
        GoogleLoginAPIView.as_view(),
        name="google-login",
    ),

    # Current logged-in user
    path(
        "auth/me/",
        AuthMeAPIView.as_view(),
        name="auth-me",
    ),

    # Refresh access token
    path(
        "auth/refresh-token/",
        AuthRefreshTokenAPIView.as_view(),
        name="auth-refresh-token",
    ),

    # Logout
    path(
        "auth/logout/",
        AuthLogoutAPIView.as_view(),
        name="auth-logout",
    ),


    # ========================================================
    # PROFILE
    # ========================================================

    path(
        "profile/",
        ProfileAPIView.as_view(),
        name="profile",
    ),

    path(
        "profile/update/",
        UpdateProfileAPIView.as_view(),
        name="profile-update",
    ),


    # ========================================================
    # CUSTOMER ADDRESSES
    # ========================================================

    # GET all addresses / POST new address
    path(
        "addresses/",
        CustomerAddressListCreateAPIView.as_view(),
        name="customer-address-list-create",
    ),

    # GET / PUT / PATCH / DELETE individual address
    path(
        "addresses/<int:pk>/",
        CustomerAddressDetailAPIView.as_view(),
        name="customer-address-detail",
    ),


    # ========================================================
    # PASSWORD RESET
    # ========================================================

    # Send password-reset OTP
    path(
        "forgot-password/",
        ForgotPasswordAPIView.as_view(),
        name="forgot-password",
    ),

    # Verify password-reset OTP
    path(
        "verify-password-otp/",
        VerifyPasswordOTPAPIView.as_view(),
        name="verify-password-otp",
    ),

    # Reset password
    path(
        "reset-password/",
        ResetPasswordAPIView.as_view(),
        name="reset-password",
    ),
]