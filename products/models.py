from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Product(models.Model):
    # =========================================================
    # STATUS CHOICES
    # =========================================================

    class ProductStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_QA = "PENDING_QA", "Pending QA"
        APPROVED = "APPROVED", "Approved"
        LIVE = "LIVE", "Live"
        REJECTED = "REJECTED", "Rejected"
        INACTIVE = "INACTIVE", "Inactive"

    class ReturnPolicy(models.TextChoices):
        RETURNABLE = "RETURNABLE", "Returnable"
        FINAL_SALE = "FINAL_SALE", "Final Sale"

    class FulfilmentLocation(models.TextChoices):
        MUMBAI_FC = "MUMBAI_FC", "Mumbai FC"
        BANGALORE_FC = "BANGALORE_FC", "Bangalore FC"
        DELHI_FC = "DELHI_FC", "Delhi FC"
        DESIGNER_STUDIO = "DESIGNER_STUDIO", "Designer Studio"

    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        FREE = "FREE", "Free Size"

    # =========================================================
    # BASIC PRODUCT INFORMATION
    # =========================================================

    product_name = models.CharField(
        max_length=255,
        verbose_name="Product Name"
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="SKU"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Product Description"
    )

    # =========================================================
    # PRODUCT CLASSIFICATION
    # =========================================================

    designer = models.CharField(
        max_length=255,
        verbose_name="Designer"
    )

    category = models.CharField(
        max_length=150,
        verbose_name="Category"
    )

    subcategory = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Subcategory"
    )

    # =========================================================
    # PRODUCT ATTRIBUTES
    # =========================================================

    colour = models.CharField(
        max_length=100,
        verbose_name="Colour"
    )

    size = models.CharField(
        max_length=20,
        choices=Size.choices,
        default=Size.FREE,
        verbose_name="Size"
    )

    material = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Material"
    )

    # =========================================================
    # PRICING
    # =========================================================

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="MRP"
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0)
        ],
        verbose_name="Selling Price"
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name="Discount Percentage"
    )

    # =========================================================
    # INVENTORY
    # =========================================================

    inventory_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Inventory Quantity"
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name="Low Stock Threshold"
    )

    # =========================================================
    # FULFILMENT
    # =========================================================

    fulfilment_location = models.CharField(
        max_length=100,
        choices=FulfilmentLocation.choices,
        verbose_name="Fulfilment Location"
    )

    fast_delivery = models.BooleanField(
        default=False,
        verbose_name="Fast Delivery"
    )

    # =========================================================
    # RETURN POLICY
    # =========================================================

    return_policy = models.CharField(
        max_length=30,
        choices=ReturnPolicy.choices,
        default=ReturnPolicy.RETURNABLE,
        verbose_name="Return Policy"
    )

    # =========================================================
    # PRODUCT STATUS
    # =========================================================

    status = models.CharField(
        max_length=30,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True,
        verbose_name="Product Status"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    is_live = models.BooleanField(
        default=False,
        verbose_name="Live on Storefront"
    )

    # =========================================================
    # PRODUCT IMAGE
    # =========================================================

    primary_image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="Primary Product Image"
    )

    # =========================================================
    # AUDIT FIELDS
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:
        db_table = "product"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["designer"]),
            models.Index(fields=["is_live"]),
            models.Index(fields=["is_active"]),
        ]

        verbose_name = "Product"
        verbose_name_plural = "Products"

    # =========================================================
    # VALIDATION
    # =========================================================

    def clean(self):
        """
        Validate product pricing.
        """

        if self.selling_price > self.mrp:
            raise ValidationError({
                "selling_price": "Selling price cannot be greater than MRP."
            })

        if self.mrp > 0:
            calculated_discount = (
                (self.mrp - self.selling_price) / self.mrp
            ) * 100

            # Allow a very small decimal difference
            if abs(
                float(self.discount_percentage) -
                float(calculated_discount)
            ) > 0.01:
                raise ValidationError({
                    "discount_percentage": (
                        "Discount percentage does not match "
                        "MRP and selling price."
                    )
                })

    # =========================================================
    # METHODS
    # =========================================================

    def __str__(self):
        return f"{self.product_name} ({self.sku})"

    # =========================================================
    # DISCOUNT AMOUNT
    # =========================================================

    @property
    def discount_amount(self):
        """
        Returns the actual discount amount.
        """

        return self.mrp - self.selling_price

    # =========================================================
    # STOCK STATUS
    # =========================================================

    @property
    def stock_status(self):
        """
        Returns the current inventory status.
        """

        if self.inventory_quantity == 0:
            return "OUT_OF_STOCK"

        if self.inventory_quantity <= self.low_stock_threshold:
            return "LOW_STOCK"

        return "IN_STOCK"

    # =========================================================
    # FAST DELIVERY
    # =========================================================

    @property
    def is_fast_delivery(self):
        """
        Returns True only when fast delivery is enabled
        and the product is currently in stock.
        """

        return (
            self.fast_delivery
            and self.inventory_quantity > 0
        )