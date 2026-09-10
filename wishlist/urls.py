from django.urls import path

from .views import WishlistSyncAPIView


urlpatterns = [

    path(
        "sync/",
        WishlistSyncAPIView.as_view(),
        name="wishlist-sync"
    ),
]