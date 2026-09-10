from rest_framework import serializers

from products.models import Product


class WishlistProductSerializer(
    serializers.ModelSerializer
):

    category = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    productName = serializers.CharField(
        source="product_name"
    )

    productType = serializers.CharField(
        source="product_type"
    )

    petType = serializers.CharField(
        source="pet_type"
    )

    isAvailable = serializers.BooleanField(
        source="is_available"
    )

    class Meta:

        model = Product

        fields = [
            "id",
            "productName",
            "description",
            "sku",
            "category",
            "brand",
            "petType",
            "productType",
            "price",
            "stock",
            "weight",
            "isAvailable",
            "image",
        ]

    def get_category(self, obj):

        if obj.category:
            return {
                "id": obj.category.id,
                "name": obj.category.category_name,
            }

        return None

    def get_brand(self, obj):

        if obj.brand:
            return {
                "id": obj.brand.id,
                "name": obj.brand.brand_name,
            }

        return None