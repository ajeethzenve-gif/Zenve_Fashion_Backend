from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import (
    Order,
    OrderItem,
)

from .serializers import (
    OrderSerializer,
    CreateOrderSerializer,
)


# ============================================================
# ORDER LIST + CREATE
#
# POST /api/orders/
# GET  /api/orders/
# ============================================================

class OrderListCreateAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    # ========================================================
    # GET /api/orders/
    # ========================================================

    def get(self, request):

        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related(
            "items"
        ).order_by(
            "-created_at"
        )

        serializer = OrderSerializer(
            orders,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ========================================================
    # POST /api/orders/
    # ========================================================

    @transaction.atomic
    def post(self, request):

        serializer = CreateOrderSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "error": "Invalid order data.",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        items = data["items"]

        discount = data.get(
            "discount",
            Decimal("0.00")
        )

        shipping = data.get(
            "shipping",
            Decimal("0.00")
        )

        payment_method = data.get(
            "paymentMethod",
            "COD"
        )

        shipping_address = data[
            "shippingAddress"
        ]

        # ====================================================
        # CALCULATE SUBTOTAL
        # ====================================================

        subtotal = Decimal("0.00")

        normalized_items = []

        for item in items:

            quantity = int(
                item.get(
                    "quantity",
                    1
                )
            )

            price = Decimal(
                str(
                    item.get(
                        "price",
                        "0"
                    )
                )
            )

            item_total = (
                price * quantity
            )

            subtotal += item_total

            normalized_items.append(
                {
                    "product_id": item[
                        "product_id"
                    ],
                    "product_name": item[
                        "product_name"
                    ],
                    "product_image": item.get(
                        "product_image"
                    ),
                    "quantity": quantity,
                    "price": price,
                    "size": item.get(
                        "size",
                        ""
                    ),
                    "color": item.get(
                        "color",
                        ""
                    ),
                }
            )

        # ====================================================
        # PREVENT NEGATIVE DISCOUNT
        # ====================================================

        if discount < Decimal("0.00"):
            discount = Decimal("0.00")

        if discount > subtotal:
            discount = subtotal

        # ====================================================
        # SHIPPING
        # ====================================================

        if shipping < Decimal("0.00"):
            shipping = Decimal("0.00")

        # ====================================================
        # TOTAL
        # ====================================================

        total = (
            subtotal
            - discount
            + shipping
        )

        if total < Decimal("0.00"):
            total = Decimal("0.00")

        # ====================================================
        # PAYMENT STATUS
        # ====================================================

        if payment_method in [
            "COD",
            "Cash on Delivery",
        ]:
            payment_status = "Pending"

        else:
            payment_status = "Pending"

        # ====================================================
        # ESTIMATED DELIVERY
        # ====================================================

        estimated_delivery = (
            timezone.localdate()
            + timedelta(days=5)
        )

        # ====================================================
        # CREATE ORDER
        # ====================================================

        order = Order.objects.create(
            user=request.user,

            subtotal=subtotal,
            discount=discount,
            shipping=shipping,
            total=total,

            payment_status=payment_status,

            payment_method=payment_method,

            order_status="Pending",

            shipping_full_name=shipping_address[
                "full_name"
            ],

            shipping_phone=shipping_address[
                "phone"
            ],

            shipping_address_line1=shipping_address[
                "address_line1"
            ],

            shipping_address_line2=shipping_address.get(
                "address_line2",
                ""
            ),

            shipping_city=shipping_address[
                "city"
            ],

            shipping_state=shipping_address[
                "state"
            ],

            shipping_country=shipping_address.get(
                "country",
                "India"
            ),

            shipping_postal_code=shipping_address[
                "postal_code"
            ],

            estimated_delivery=estimated_delivery,
        )

        # ====================================================
        # CREATE ORDER ITEMS
        # ====================================================

        order_items = []

        for item in normalized_items:

            order_items.append(
                OrderItem(
                    order=order,

                    product_id=item[
                        "product_id"
                    ],

                    product_name=item[
                        "product_name"
                    ],

                    product_image=item[
                        "product_image"
                    ],

                    quantity=item[
                        "quantity"
                    ],

                    price=item[
                        "price"
                    ],

                    size=item[
                        "size"
                    ],

                    color=item[
                        "color"
                    ],

                    total=(
                        item["price"]
                        * item["quantity"]
                    ),
                )
            )

        OrderItem.objects.bulk_create(
            order_items
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        response_serializer = OrderSerializer(
            order,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# ORDER DETAIL
#
# GET /api/orders/<idOrNumber>/
# ============================================================

class OrderDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, idOrNumber):

        # ====================================================
        # FIND BY NUMERIC ID
        # ====================================================

        order = None

        if str(idOrNumber).isdigit():

            order = Order.objects.filter(
                id=int(idOrNumber),
                user=request.user,
            ).prefetch_related(
                "items"
            ).first()

        # ====================================================
        # FIND BY ORDER NUMBER
        # ====================================================

        if order is None:

            order = Order.objects.filter(
                order_number__iexact=str(
                    idOrNumber
                ),
                user=request.user,
            ).prefetch_related(
                "items"
            ).first()

        # ====================================================
        # NOT FOUND
        # ====================================================

        if order is None:

            return Response(
                {
                    "error": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ====================================================
        # SERIALIZE
        # ====================================================

        serializer = OrderSerializer(
            order,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )