from django.db import models
from django.contrib.auth.models import User


class CartItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    product_id = models.IntegerField()

    product_name = models.CharField(
        max_length=255
    )

    product_image = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    size = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    color = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "product_id",
                    "size",
                    "color"
                ],
                name="unique_user_cart_product_variant"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product_name}"