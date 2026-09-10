from django.contrib import admin
from django.urls import path, include


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "api/accounts/",
        include("accounts.urls")
    ),

    path(
        "api/designers/",
        include("designers.urls")
    ),

    path(
        "api/products/",
        include("products.urls")
    ),

    path(
        "api/orders/",
        include("orders.urls")
    ),

    path(
        "api/payments/",
        include("payments.urls")
    ),

    path(
        "api/cart/",
        include("cart.urls")
    ),

    path(
        "api/wishlist/",
        include("wishlist.urls")
    ),
]