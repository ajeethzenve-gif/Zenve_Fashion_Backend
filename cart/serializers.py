from rest_framework import serializers

from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):

    productId = serializers.IntegerField(
        source="product_id"
    )

    productName = serializers.CharField(
        source="product_name"
    )

    productImage = serializers.CharField(
        source="product_image",
        required=False,
        allow_null=True,
        allow_blank=True
    )

    class Meta:
        model = CartItem

        fields = [
            "productId",
            "productName",
            "productImage",
            "quantity",
            "price",
            "size",
            "color",
        ]


class CartSyncSerializer(serializers.Serializer):

    items = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate_items(self, value):

        for item in value:

            if not item.get("productId"):
                raise serializers.ValidationError(
                    "Each cart item must contain productId."
                )

            try:
                quantity = int(
                    item.get("quantity", 1)
                )
            except (TypeError, ValueError):

                raise serializers.ValidationError(
                    "Quantity must be a valid number."
                )

            if quantity < 0:

                raise serializers.ValidationError(
                    "Quantity cannot be negative."
                )

            if item.get("price") is None:

                raise serializers.ValidationError(
                    "Each cart item must contain price."
                )

        return value


class PromoSerializer(serializers.Serializer):

    code = serializers.CharField(
        required=True,
        max_length=100
    )