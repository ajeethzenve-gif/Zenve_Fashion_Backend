from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from products.models import Product

from .models import WishlistItem
from .serializers import WishlistProductSerializer


class WishlistSyncAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        product_ids = request.data.get(
            "productIds"
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if product_ids is None:

            return Response(
                {
                    "detail": (
                        "productIds is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(product_ids, list):

            return Response(
                {
                    "detail": (
                        "productIds must be an array."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # CONVERT IDs
        # ----------------------------------------------------

        cleaned_ids = []

        for product_id in product_ids:

            try:
                product_id = int(product_id)

            except (TypeError, ValueError):

                return Response(
                    {
                        "detail": (
                            "productIds must contain "
                            "valid product IDs."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if product_id not in cleaned_ids:
                cleaned_ids.append(product_id)

        # ----------------------------------------------------
        # VERIFY PRODUCTS EXIST
        # ----------------------------------------------------

        products = Product.objects.filter(
            id__in=cleaned_ids
        )

        existing_ids = set(
            products.values_list(
                "id",
                flat=True
            )
        )

        invalid_ids = [
            product_id
            for product_id in cleaned_ids
            if product_id not in existing_ids
        ]

        if invalid_ids:

            return Response(
                {
                    "detail": "Some products do not exist.",
                    "invalidProductIds": invalid_ids,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # SYNCHRONIZE WISHLIST
        # ----------------------------------------------------

        with transaction.atomic():

            WishlistItem.objects.filter(
                user=request.user
            ).exclude(
                product_id__in=cleaned_ids
            ).delete()

            existing_wishlist_ids = set(
                WishlistItem.objects.filter(
                    user=request.user,
                    product_id__in=cleaned_ids
                ).values_list(
                    "product_id",
                    flat=True
                )
            )

            new_items = []

            for product_id in cleaned_ids:

                if product_id not in existing_wishlist_ids:

                    new_items.append(
                        WishlistItem(
                            user=request.user,
                            product_id=product_id
                        )
                    )

            if new_items:

                WishlistItem.objects.bulk_create(
                    new_items
                )

        # ----------------------------------------------------
        # RETURN PRODUCTS
        # ----------------------------------------------------

        products = Product.objects.filter(
            id__in=cleaned_ids
        )

        # Keep the same order as productIds
        product_map = {
            product.id: product
            for product in products
        }

        ordered_products = [
            product_map[product_id]
            for product_id in cleaned_ids
            if product_id in product_map
        ]

        return Response(
            WishlistProductSerializer(
                ordered_products,
                many=True,
                context={
                    "request": request
                }
            ).data,
            status=status.HTTP_200_OK
        )