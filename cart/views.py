from decimal import Decimal

from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import CartItem
from .serializers import (
    CartItemSerializer,
    CartSyncSerializer,
    PromoSerializer,
)


# ============================================================
# CART SYNC
# ============================================================

class CartSyncAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CartSyncSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        items = serializer.validated_data["items"]

        with transaction.atomic():

            for item in items:

                product_id = int(
                    item["productId"]
                )

                quantity = int(
                    item.get("quantity", 1)
                )

                size = item.get("size") or None
                color = item.get("color") or None

                # ------------------------------------------------
                # REMOVE ITEM IF QUANTITY IS ZERO
                # ------------------------------------------------

                if quantity == 0:

                    CartItem.objects.filter(
                        user=request.user,
                        product_id=product_id,
                        size=size,
                        color=color
                    ).delete()

                    continue

                # ------------------------------------------------
                # CREATE / UPDATE
                # ------------------------------------------------

                cart_item, created = (
                    CartItem.objects.update_or_create(
                        user=request.user,
                        product_id=product_id,
                        size=size,
                        color=color,
                        defaults={
                            "product_name": item.get(
                                "productName",
                                ""
                            ),

                            "product_image": item.get(
                                "productImage"
                            ),

                            "quantity": quantity,

                            "price": Decimal(
                                str(item["price"])
                            ),
                        }
                    )
                )

        cart_items = CartItem.objects.filter(
            user=request.user
        )

        return Response(
            CartItemSerializer(
                cart_items,
                many=True
            ).data,
            status=status.HTTP_200_OK
        )


# ============================================================
# PROMO
# ============================================================

class CartPromoAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = PromoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        code = serializer.validated_data[
            "code"
        ].strip().upper()

        # ----------------------------------------------------
        # PROMO CODES
        # ----------------------------------------------------
        #
        # Replace these with your Coupon model/API later.
        #

        promo_codes = {
            "ZENVE10": 10,
            "FASHION15": 15,
            "WELCOME20": 20,
        }

        discount = promo_codes.get(code)

        if discount is None:

            return Response(
                {
                    "valid": False,
                    "discountPercentage": 0,
                    "message": "Invalid promo code.",
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "valid": True,
                "discountPercentage": discount,
                "message": (
                    f"Promo code applied successfully. "
                    f"You received {discount}% discount."
                ),
            },
            status=status.HTTP_200_OK
        )