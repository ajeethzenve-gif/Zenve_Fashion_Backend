from django.urls import path
from .views import (RegisterAPIView,
                    LoginAPIView,
                    GoogleLoginAPIView,
                    ForgotPasswordAPIView,
                    VerifyPasswordOTPAPIView,
                    ResetPasswordAPIView,

                    )

urlpatterns = [

    path("register/",RegisterAPIView.as_view(),name="register"),
    path("login/",LoginAPIView.as_view(),name="login"),
    path("google-login/",GoogleLoginAPIView.as_view()),
    path("forgot-password/",ForgotPasswordAPIView.as_view(),name="forgot-password"),
    path("verify-otp/",VerifyPasswordOTPAPIView.as_view(),name="verify-otp"),
    path("reset-password/",ResetPasswordAPIView.as_view(),name="reset-password"),

]