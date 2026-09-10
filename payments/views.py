import hmac
import hashlib
import logging
import os
from decimal import Decimal

import razorpay

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from orders.models import Order
from .models import Payment
from .serializers import (
    PaymentInitiateSerializer,
    PaymentVerifySerializer,
)


logger = logging.getLogger(__name__)


# ============================================================
# RAZORPAY CLIENT
# ============================================================

def get_razorpay_client():

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise ValueError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
            "must be configured in the environment."
        )

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


# ============================================================
# FIND ORDER
# ============================================================

def get_user_order(user, order_id):

    """
    Supports:

        /payments with orderId = "1"

    or:

        orderId = "ZNV-2026-1001"
    """

    try:
        if str(order_id).isdigit():

            return get_object_or_404(
                Order,
                id=int(order_id),
                user=user
            )

    except (ValueError, TypeError):
        pass

    return get_object_or_404(
        Order,
        order_number=str(order_id),
        user=user
    )


# ============================================================
# INITIATE PAYMENT
# ============================================================

class PaymentInitiateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = PaymentInitiateSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["orderId"]
        requested_amount = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]
        gateway = serializer.validated_data["gateway"]

        # ----------------------------------------------------
        # FIND ORDER
        # ----------------------------------------------------

        order = get_user_order(
            request.user,
            order_id
        )

        # ----------------------------------------------------
        # VERIFY AMOUNT AGAINST ORDER
        # ----------------------------------------------------

        order_amount = Decimal(str(order.total))

        if requested_amount != order_amount:

            return Response(
                {
                    "detail": (
                        "Payment amount does not match "
                        "the order total."
                    ),
                    "orderAmount": float(order_amount),
                    "requestedAmount": float(requested_amount),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # PREVENT PAYMENT FOR ALREADY PAID ORDER
        # ----------------------------------------------------

        if order.payment_status == "Paid":

            return Response(
                {
                    "detail": "Order has already been paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # CASH ON DELIVERY
        # ====================================================

        if gateway == "cod":

            with transaction.atomic():

                payment = Payment.objects.create(
                    order=order,
                    user=request.user,
                    payment_id=f"COD-{order.id}",
                    gateway="cod",
                    amount=order_amount,
                    currency=currency,
                    status="authorized",
                )

                order.payment_status = "Pending"

                if hasattr(order, "payment_method"):
                    order.payment_method = "COD"

                order.save()

            return Response(
                {
                    "paymentId": payment.payment_id,
                    "orderId": str(order.id),
                    "amount": float(order_amount),
                    "currency": currency,
                },
                status=status.HTTP_201_CREATED
            )

        # ====================================================
        # RAZORPAY
        # ====================================================

        if gateway == "razorpay":

            try:

                client = get_razorpay_client()

                # Razorpay requires amount in paise
                amount_in_paise = int(
                    order_amount * Decimal("100")
                )

                razorpay_order = client.order.create(
                    {
                        "amount": amount_in_paise,
                        "currency": currency,
                        "receipt": str(
                            order.order_number
                        ),
                        "notes": {
                            "order_id": str(order.id),
                            "order_number": str(
                                order.order_number
                            ),
                            "user_id": str(
                                request.user.id
                            ),
                        },
                    }
                )

                payment = Payment.objects.create(
                    order=order,
                    user=request.user,
                    payment_id=None,
                    gateway="razorpay",
                    amount=order_amount,
                    currency=currency,
                    gateway_order_id=razorpay_order["id"],
                    status="created",
                )

                if hasattr(order, "payment_method"):
                    order.payment_method = "Razorpay"

                order.save()

                return Response(
                    {
                        "paymentId": razorpay_order["id"],
                        "gatewayKeyId": os.getenv(
                            "RAZORPAY_KEY_ID"
                        ),
                        "orderId": str(order.id),
                        "amount": float(order_amount),
                        "currency": currency,
                    },
                    status=status.HTTP_201_CREATED
                )

            except Exception as exc:

                logger.exception(
                    "Razorpay payment initiation failed"
                )

                return Response(
                    {
                        "detail": (
                            "Unable to initiate Razorpay payment."
                        ),
                        "error": str(exc),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # ====================================================
        # STRIPE
        # ====================================================

        if gateway == "stripe":

            return Response(
                {
                    "detail": (
                        "Stripe payment gateway is not "
                        "configured yet."
                    ),
                    "gateway": "stripe",
                },
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        return Response(
            {
                "detail": "Unsupported payment gateway."
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# VERIFY PAYMENT
# ============================================================

class PaymentVerifyAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = PaymentVerifySerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["orderId"]
        payment_id = serializer.validated_data["paymentId"]
        signature = serializer.validated_data.get(
            "signature"
        )

        # ----------------------------------------------------
        # FIND ORDER
        # ----------------------------------------------------

        order = get_user_order(
            request.user,
            order_id
        )

        # ====================================================
        # FIND PAYMENT
        # ====================================================

        payment = Payment.objects.filter(
            order=order,
            user=request.user
        ).order_by(
            "-created_at"
        ).first()

        if not payment:

            return Response(
                {
                    "success": False,
                    "status": "failed",
                    "message": "Payment record not found.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ====================================================
        # COD
        # ====================================================

        if payment.gateway == "cod":

            payment.status = "authorized"
            payment.payment_id = payment_id
            payment.save()

            return Response(
                {
                    "success": True,
                    "status": "authorized",
                    "message": (
                        "Cash on Delivery payment "
                        "authorized successfully."
                    ),
                },
                status=status.HTTP_200_OK
            )

        # ====================================================
        # RAZORPAY
        # ====================================================

        if payment.gateway == "razorpay":

            if not signature:

                payment.status = "failed"
                payment.save()

                return Response(
                    {
                        "success": False,
                        "status": "failed",
                        "message": (
                            "Razorpay signature is required."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not payment.gateway_order_id:

                payment.status = "failed"
                payment.save()

                return Response(
                    {
                        "success": False,
                        "status": "failed",
                        "message": (
                            "Razorpay order ID is missing."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # VERIFY RAZORPAY SIGNATURE
            # ------------------------------------------------

            try:

                client = get_razorpay_client()

                client.utility.verify_payment_signature(
                    {
                        "razorpay_order_id": (
                            payment.gateway_order_id
                        ),
                        "razorpay_payment_id": (
                            payment_id
                        ),
                        "razorpay_signature": (
                            signature
                        ),
                    }
                )

            except Exception:

                payment.status = "failed"
                payment.signature = signature
                payment.payment_id = payment_id
                payment.save()

                order.payment_status = "Failed"
                order.save()

                return Response(
                    {
                        "success": False,
                        "status": "failed",
                        "message": (
                            "Payment signature verification failed."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            with transaction.atomic():

                payment.payment_id = payment_id
                payment.signature = signature
                payment.status = "captured"
                payment.save()

                order.payment_status = "Paid"

                if hasattr(order, "payment_method"):
                    order.payment_method = "Razorpay"

                order.save()

            return Response(
                {
                    "success": True,
                    "status": "captured",
                    "message": (
                        "Payment verified successfully."
                    ),
                },
                status=status.HTTP_200_OK
            )

        # ====================================================
        # STRIPE
        # ====================================================

        if payment.gateway == "stripe":

            return Response(
                {
                    "success": False,
                    "status": "failed",
                    "message": (
                        "Stripe verification is not "
                        "configured yet."
                    ),
                },
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        return Response(
            {
                "success": False,
                "status": "failed",
                "message": "Unsupported payment gateway.",
            },
            status=status.HTTP_400_BAD_REQUEST
        )