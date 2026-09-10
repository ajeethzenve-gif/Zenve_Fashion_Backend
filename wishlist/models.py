from django.db import models
from django.contrib.auth.models import User


class WishlistItem(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    product_id = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "product_id"
                ],
                name="unique_user_wishlist_product"
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"Product {self.product_id}"
        )