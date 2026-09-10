from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Product serializer used by:

    GET /products/
    GET /products/<slug>/
    GET /products/atelier-picks/
    GET /products/category/<category>/
    GET /products/<productId>/related/
    """

    category_name = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()

    slug = serializers.SerializerMethodField()

    inStock = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = Product

        fields = [
            "id",
            "slug",

            "product_name",
            "description",

            "sku",

            "category",
            "category_name",

            "brand",
            "brand_name",

            "pet_type",
            "product_type",

            "price",
            "stock",
            "weight",

            "is_available",
            "inStock",

            "image",
            "badges",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "category_name",
            "brand_name",
            "inStock",
            "badges",
            "created_at",
            "updated_at",
        ]

    # ========================================================
    # CATEGORY
    # ========================================================

    def get_category_name(self, obj):
        if obj.category:
            return obj.category.category_name

        return None

    # ========================================================
    # BRAND
    # ========================================================

    def get_brand_name(self, obj):
        if obj.brand:
            return obj.brand.brand_name

        return None

    # ========================================================
    # SLUG
    # ========================================================

    def get_slug(self, obj):
        """
        Uses a slug field if your Product model has one.

        If your existing Product model does not have a slug,
        product ID is used as a fallback.
        """

        if hasattr(obj, "slug") and obj.slug:
            return obj.slug

        from django.utils.text import slugify

        if obj.product_name:
            return slugify(
                f"{obj.product_name}-{obj.id}"
            )

        return str(obj.id)

    # ========================================================
    # STOCK
    # ========================================================

    def get_inStock(self, obj):
        return (
            obj.stock is not None
            and obj.stock > 0
            and obj.is_available
        )

    # ========================================================
    # BADGES
    # ========================================================

    def get_badges(self, obj):
        """
        Returns badges expected by the frontend.

        This does not require an additional database field.
        """

        badges = []

        if obj.stock is not None and obj.stock <= 5 and obj.stock > 0:
            badges.append("Low Stock")

        if obj.stock == 0:
            badges.append("Out of Stock")

        if not obj.is_available:
            badges.append("Unavailable")

        return badges