from django.urls import path

from .views import (
    ProductListAPIView,
    ProductDetailBySlugAPIView,
    AtelierPicksAPIView,
    ProductCategoryAPIView,
    RelatedProductsAPIView,
)


urlpatterns = [

    # ========================================================
    # ATELIER PICKS
    # GET /api/products/atelier-picks/
    # ========================================================

    path(
        "atelier-picks/",
        AtelierPicksAPIView.as_view(),
        name="atelier-picks",
    ),

    # ========================================================
    # PRODUCT CATEGORY
    # GET /api/products/category/<category>/
    #
    # category:
    #   people
    #   pets
    #   twin
    # ========================================================

    path(
        "category/<str:category>/",
        ProductCategoryAPIView.as_view(),
        name="product-category",
    ),

    # ========================================================
    # RELATED PRODUCTS
    # GET /api/products/<productId>/related/
    # ========================================================

    path(
        "<int:productId>/related/",
        RelatedProductsAPIView.as_view(),
        name="related-products",
    ),

    # ========================================================
    # PRODUCT DETAIL BY SLUG
    # GET /api/products/<slug>/
    # ========================================================

    path(
        "<slug>/",
        ProductDetailBySlugAPIView.as_view(),
        name="product-detail-by-slug",
    ),

    # ========================================================
    # PRODUCT LIST
    # GET /api/products/
    # ========================================================

    path(
        "",
        ProductListAPIView.as_view(),
        name="product-list",
    ),
]