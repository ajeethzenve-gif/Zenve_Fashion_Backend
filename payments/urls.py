from django.urls import path

from .views import (
    PaymentInitiateAPIView,
    PaymentVerifyAPIView,
)


urlpatterns = [
    path(
        "initiate/",
        PaymentInitiateAPIView.as_view(),
        name="payment-initiate",
    ),

    path(
        "verify/",
        PaymentVerifyAPIView.as_view(),
        name="payment-verify",
    ),
]