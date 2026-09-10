from django.db import models
from django.contrib.auth.models import User
from orders.models import Order


class Payment(models.Model):

    GATEWAY_CHOICES = (
        ("razorpay", "Razorpay"),
        ("stripe", "Stripe"),
        ("cod", "Cash on Delivery"),
    )

    STATUS_CHOICES = (
        ("created", "Created"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True
    )

    gateway = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="INR"
    )

    signature = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    gateway_order_id = models.CharField(
        max_length=255,
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
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.gateway} - {self.amount}"