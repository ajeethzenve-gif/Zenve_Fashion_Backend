from rest_framework import serializers

from .models import (
    Order,
    OrderItem,
)


# ============================================================
# SHIPPING ADDRESS SERIALIZER
# ============================================================

class ShippingAddressSerializer(serializers.Serializer):

    full_name = serializers.CharField(
        max_length=100
    )

    phone = serializers.CharField(
        max_length=15
    )

    address_line1 = serializers.CharField(
        max_length=255
    )

    address_line2 = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )

    city = serializers.CharField(
        max_length=100
    )

    state = serializers.CharField(
        max_length=100
    )

    country = serializers.CharField(
        max_length=100,
        required=False,
        default="India"
    )

    postal_code = serializers.CharField(
        max_length=10
    )


# ============================================================
# ORDER ITEM SERIALIZER
# ============================================================

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem

        fields = [
            "id",
            "product_id",
            "product_name",
            "product_image",
            "quantity",
            "price",
            "total",
            "size",
            "color",
        ]

        read_only_fields = [
            "id",
            "total",
        ]


# ============================================================
# ORDER SERIALIZER
# ============================================================

class OrderSerializer(serializers.ModelSerializer):

    # --------------------------------------------------------
    # Frontend: userId
    # Backend: user
    # --------------------------------------------------------

    userId = serializers.IntegerField(
        source="user.id",
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: orderNumber
    # Backend: order_number
    # --------------------------------------------------------

    orderNumber = serializers.CharField(
        source="order_number",
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: paymentStatus
    # Backend: payment_status
    # --------------------------------------------------------

    paymentStatus = serializers.CharField(
        source="payment_status",
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: orderStatus
    # Backend: order_status
    # --------------------------------------------------------

    orderStatus = serializers.CharField(
        source="order_status",
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: paymentMethod
    # Backend: payment_method
    # --------------------------------------------------------

    paymentMethod = serializers.CharField(
        source="payment_method",
        read_only=True
    )

    # --------------------------------------------------------
    # Order items
    # --------------------------------------------------------

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: shippingAddress
    # --------------------------------------------------------

    shippingAddress = serializers.SerializerMethodField()

    # --------------------------------------------------------
    # Frontend: estimatedDelivery
    # --------------------------------------------------------

    estimatedDelivery = serializers.DateField(
        source="estimated_delivery",
        read_only=True
    )

    # --------------------------------------------------------
    # Frontend: createdAt
    # --------------------------------------------------------

    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "orderNumber",
            "userId",
            "items",
            "subtotal",
            "discount",
            "shipping",
            "total",
            "paymentStatus",
            "orderStatus",
            "paymentMethod",
            "shippingAddress",
            "estimatedDelivery",
            "createdAt",
        ]

        read_only_fields = [
            "id",
            "orderNumber",
            "userId",
            "items",
            "subtotal",
            "discount",
            "shipping",
            "total",
            "paymentStatus",
            "orderStatus",
            "estimatedDelivery",
            "createdAt",
        ]

    # ========================================================
    # SHIPPING ADDRESS
    # ========================================================

    def get_shippingAddress(self, obj):

        return {
            "full_name": obj.shipping_full_name,
            "phone": obj.shipping_phone,
            "address_line1": obj.shipping_address_line1,
            "address_line2": obj.shipping_address_line2,
            "city": obj.shipping_city,
            "state": obj.shipping_state,
            "country": obj.shipping_country,
            "postal_code": obj.shipping_postal_code,
        }


# ============================================================
# CREATE ORDER SERIALIZER
# ============================================================

class CreateOrderSerializer(serializers.Serializer):

    # --------------------------------------------------------
    # Order items
    # --------------------------------------------------------

    items = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    # --------------------------------------------------------
    # Discount
    # --------------------------------------------------------

    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=0
    )

    # --------------------------------------------------------
    # Shipping
    # --------------------------------------------------------

    shipping = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=0
    )

    # --------------------------------------------------------
    # Payment method
    # --------------------------------------------------------

    paymentMethod = serializers.CharField(
        required=False,
        default="COD"
    )

    # --------------------------------------------------------
    # Shipping address
    # --------------------------------------------------------

    shippingAddress = ShippingAddressSerializer(
        required=True
    )

    # ========================================================
    # VALIDATE ITEMS
    # ========================================================

    def validate_items(self, value):

        if not value:
            raise serializers.ValidationError(
                "Order must contain at least one item."
            )

        for item in value:

            if not item.get("product_id"):
                raise serializers.ValidationError(
                    "Each item must contain product_id."
                )

            if not item.get("product_name"):
                raise serializers.ValidationError(
                    "Each item must contain product_name."
                )

            quantity = item.get(
                "quantity",
                1
            )

            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "Quantity must be a valid number."
                )

            if quantity <= 0:
                raise serializers.ValidationError(
                    "Quantity must be greater than zero."
                )

            if item.get("price") is None:
                raise serializers.ValidationError(
                    "Each item must contain price."
                )

        return value

    # ========================================================
    # VALIDATE PAYMENT METHOD
    # ========================================================

    def validate_paymentMethod(self, value):

        allowed_methods = [
            "COD",
            "Cash on Delivery",
            "Razorpay",
            "Wallet",
            "UPI",
            "Card",
            "Net Banking",
        ]

        if value not in allowed_methods:
            raise serializers.ValidationError(
                "Invalid payment method."
            )

        return value

    # ========================================================
    # VALIDATE DISCOUNT
    # ========================================================

    def validate_discount(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Discount cannot be negative."
            )

        return value

    # ========================================================
    # VALIDATE SHIPPING
    # ========================================================

    def validate_shipping(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Shipping cannot be negative."
            )

        return value