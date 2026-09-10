from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Product
from .serializers import ProductSerializer


# ============================================================
# HELPER
# ============================================================

def get_product_slug(product):
    """
    Generate the same slug used by ProductSerializer.
    """

    if hasattr(product, "slug") and product.slug:
        return product.slug

    return slugify(
        f"{product.product_name}-{product.id}"
    )


# ============================================================
# GET /products
# ============================================================

class ProductListAPIView(APIView):
    """
    GET /products/

    Supported query parameters:

    category
    audience
    occasion
    collection
    subCategory
    minPrice
    maxPrice
    sizes
    colors
    badges
    inStockOnly
    searchQuery
    sort
    """

    permission_classes = [AllowAny]

    def get(self, request):

        products = Product.objects.all()

        # ====================================================
        # CATEGORY
        # ====================================================

        category = request.query_params.get("category")

        if category:
            products = products.filter(
                Q(category__category_name__iexact=category)
                |
                Q(product_type__iexact=category)
            )

        # ====================================================
        # AUDIENCE
        # ====================================================

        audience = request.query_params.get("audience")

        if audience:
            audience = audience.strip()

            products = products.filter(
                Q(pet_type__iexact=audience)
                |
                Q(product_type__iexact=audience)
            )

        # ====================================================
        # OCCASION
        # ====================================================

        occasion = request.query_params.get("occasion")

        if occasion:
            products = products.filter(
                Q(product_type__icontains=occasion)
                |
                Q(description__icontains=occasion)
                |
                Q(product_name__icontains=occasion)
            )

        # ====================================================
        # COLLECTION
        # ====================================================

        collection = request.query_params.get("collection")

        if collection:
            products = products.filter(
                Q(product_type__icontains=collection)
                |
                Q(product_name__icontains=collection)
                |
                Q(description__icontains=collection)
            )

        # ====================================================
        # SUB CATEGORY
        # ====================================================

        sub_category = request.query_params.get("subCategory")

        if sub_category:
            products = products.filter(
                Q(product_type__icontains=sub_category)
                |
                Q(product_name__icontains=sub_category)
            )

        # ====================================================
        # MIN PRICE
        # ====================================================

        min_price = request.query_params.get("minPrice")

        if min_price:
            try:
                products = products.filter(
                    price__gte=Decimal(min_price)
                )
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": "Invalid minPrice."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ====================================================
        # MAX PRICE
        # ====================================================

        max_price = request.query_params.get("maxPrice")

        if max_price:
            try:
                products = products.filter(
                    price__lte=Decimal(max_price)
                )
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": "Invalid maxPrice."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ====================================================
        # SIZES
        # ====================================================

        sizes = request.query_params.get("sizes")

        if sizes:
            size_values = [
                value.strip()
                for value in sizes.split(",")
                if value.strip()
            ]

            size_query = Q()

            for size in size_values:
                size_query |= Q(
                    description__icontains=size
                )

            if size_query:
                products = products.filter(size_query)

        # ====================================================
        # COLORS
        # ====================================================

        colors = request.query_params.get("colors")

        if colors:
            color_values = [
                value.strip()
                for value in colors.split(",")
                if value.strip()
            ]

            color_query = Q()

            for color in color_values:
                color_query |= Q(
                    product_name__icontains=color
                )

                color_query |= Q(
                    description__icontains=color
                )

            if color_query:
                products = products.filter(color_query)

        # ====================================================
        # BADGES
        # ====================================================

        badges = request.query_params.get("badges")

        if badges:
            badge_values = [
                value.strip().lower()
                for value in badges.split(",")
                if value.strip()
            ]

            if "in stock" in badge_values:
                products = products.filter(
                    stock__gt=0,
                    is_available=True,
                )

            if "out of stock" in badge_values:
                products = products.filter(
                    stock=0
                )

            if "low stock" in badge_values:
                products = products.filter(
                    stock__gt=0,
                    stock__lte=5,
                )

        # ====================================================
        # IN STOCK ONLY
        # ====================================================

        in_stock_only = request.query_params.get(
            "inStockOnly"
        )

        if str(in_stock_only).lower() in [
            "true",
            "1",
            "yes",
        ]:
            products = products.filter(
                stock__gt=0,
                is_available=True,
            )

        # ====================================================
        # SEARCH
        # ====================================================

        search_query = request.query_params.get(
            "searchQuery"
        )

        if search_query:
            search_query = search_query.strip()

            products = products.filter(
                Q(product_name__icontains=search_query)
                |
                Q(description__icontains=search_query)
                |
                Q(sku__icontains=search_query)
                |
                Q(
                    category__category_name__icontains=
                    search_query
                )
                |
                Q(
                    brand__brand_name__icontains=
                    search_query
                )
                |
                Q(
                    product_type__icontains=
                    search_query
                )
                |
                Q(
                    pet_type__icontains=
                    search_query
                )
            )

        # ====================================================
        # SORT
        # ====================================================

        sort = request.query_params.get("sort")

        if sort:

            sort_map = {
                "priceAsc": "price",
                "priceDesc": "-price",
                "price-low-high": "price",
                "price-high-low": "-price",

                "newest": "-created_at",
                "oldest": "created_at",

                "nameAsc": "product_name",
                "nameDesc": "-product_name",

                "name-asc": "product_name",
                "name-desc": "-product_name",

                "stockAsc": "stock",
                "stockDesc": "-stock",
            }

            order_field = sort_map.get(sort)

            if order_field:
                products = products.order_by(
                    order_field
                )
            else:
                products = products.order_by(
                    "-created_at"
                )

        else:
            products = products.order_by(
                "-created_at"
            )

        # ====================================================
        # SERIALIZE
        # ====================================================

        serializer = ProductSerializer(
            products,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET /products/:slug
# ============================================================

class ProductDetailBySlugAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, slug):

        products = Product.objects.all()

        # ----------------------------------------------------
        # First try actual slug field
        # ----------------------------------------------------

        product = None

        if hasattr(Product, "slug"):

            product = products.filter(
                slug=slug
            ).first()

        # ----------------------------------------------------
        # Fallback to generated slug
        # ----------------------------------------------------

        if product is None:

            for item in products:

                if get_product_slug(item) == slug:
                    product = item
                    break

        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if product is None:

            return Response(
                {
                    "detail": "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(
            product,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET /products/atelier-picks
# ============================================================

class AtelierPicksAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        products = Product.objects.filter(
            is_available=True,
            stock__gt=0,
        )

        # Prefer products associated with fashion/designer
        # related product types.
        atelier_products = products.filter(
            Q(product_type__icontains="Fashion")
            |
            Q(product_type__icontains="Designer")
            |
            Q(product_type__icontains="Atelier")
            |
            Q(description__icontains="atelier")
            |
            Q(description__icontains="designer")
        )

        # If no atelier-specific products exist,
        # return available products rather than an empty list.
        if atelier_products.exists():
            products = atelier_products

        products = products.order_by(
            "-created_at"
        )[:20]

        serializer = ProductSerializer(
            products,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET /products/category/:category
# ============================================================

class ProductCategoryAPIView(APIView):

    permission_classes = [AllowAny]

    VALID_CATEGORIES = [
        "people",
        "pets",
        "twin",
    ]

    def get(self, request, category):

        category = category.lower().strip()

        if category not in self.VALID_CATEGORIES:

            return Response(
                {
                    "error": (
                        "Invalid category. "
                        "Use people, pets, or twin."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = Product.objects.filter(
            is_available=True
        )

        # ====================================================
        # PEOPLE
        # ====================================================

        if category == "people":

            products = products.filter(
                Q(pet_type__iexact="People")
                |
                Q(pet_type__iexact="Human")
                |
                Q(product_type__icontains="People")
                |
                Q(product_type__icontains="Human")
                |
                Q(product_name__icontains="People")
                |
                Q(product_name__icontains="Human")
            )

        # ====================================================
        # PETS
        # ====================================================

        elif category == "pets":

            products = products.filter(
                Q(pet_type__iexact="Dog")
                |
                Q(pet_type__iexact="Cat")
                |
                Q(pet_type__iexact="Pet")
                |
                Q(product_type__icontains="Pet")
                |
                Q(product_type__icontains="Dog")
                |
                Q(product_type__icontains="Cat")
            )

        # ====================================================
        # TWIN
        # ====================================================

        elif category == "twin":

            products = products.filter(
                Q(product_type__icontains="Twin")
                |
                Q(product_name__icontains="Twin")
                |
                Q(description__icontains="Twin")
            )

        products = products.order_by(
            "-created_at"
        )

        serializer = ProductSerializer(
            products,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET /products/:productId/related
# ============================================================

class RelatedProductsAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, productId):

        product = get_object_or_404(
            Product,
            pk=productId
        )

        limit = request.query_params.get(
            "limit",
            8
        )

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 8

        # Keep limit safe
        limit = max(
            1,
            min(limit, 50)
        )

        category = request.query_params.get(
            "category"
        )

        related = Product.objects.filter(
            is_available=True
        ).exclude(
            pk=product.pk
        )

        # ====================================================
        # EXPLICIT CATEGORY
        # ====================================================

        if category:

            related = related.filter(
                Q(
                    category__category_name__iexact=
                    category
                )
                |
                Q(
                    product_type__iexact=
                    category
                )
            )

        # ====================================================
        # SAME PRODUCT CATEGORY
        # ====================================================

        elif product.category:

            related = related.filter(
                category=product.category
            )

        # ====================================================
        # FALLBACK: SAME PRODUCT TYPE
        # ====================================================

        elif product.product_type:

            related = related.filter(
                product_type__iexact=
                product.product_type
            )

        # ====================================================
        # ORDER
        # ====================================================

        related = related.order_by(
            "-created_at"
        )[:limit]

        serializer = ProductSerializer(
            related,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )