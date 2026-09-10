from django.urls import path

from .views import (
    OrderListCreateAPIView,
    OrderDetailAPIView,
)

urlpatterns = [

    # ========================================================
    # GET  /api/orders/
    # POST /api/orders/
    # ========================================================

    path(
        "",
        OrderListCreateAPIView.as_view(),
        name="order-list-create",
    ),

    # ========================================================
    # GET /api/orders/<idOrNumber>/
    # ========================================================

    path(
        "<str:idOrNumber>/",
        OrderDetailAPIView.as_view(),
        name="order-detail",
    ),
]