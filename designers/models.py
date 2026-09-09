from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)


class Designer(models.Model):
    # =========================================================
    # ONBOARDING / PIPELINE STAGES
    # =========================================================

    class Stage(models.TextChoices):
        LEAD = "LEAD", "Lead"
        QUALIFIED = "QUALIFIED", "Qualified"
        PORTFOLIO = "PORTFOLIO", "Portfolio"
        REVIEW = "REVIEW", "Review"
        APPROVED = "APPROVED", "Approved"
        CONTRACT = "CONTRACT", "Contract"
        SIGNED = "SIGNED", "Signed"
        LIVE = "LIVE", "Live"
        ACTIVE = "ACTIVE", "Active"
        REJECTED = "REJECTED", "Rejected"
        INACTIVE = "INACTIVE", "Inactive"

    # =========================================================
    # DESIGNER TIER
    # =========================================================

    class Tier(models.TextChoices):
        CORE = "CORE", "Core"
        PREMIUM = "PREMIUM", "Premium"
        EMERGING = "EMERGING", "Emerging"

    # =========================================================
    # KYC STATUS
    # =========================================================

    class KYCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    # =========================================================
    # BASIC DESIGNER INFORMATION
    # =========================================================

    designer_code = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name="Designer Code",
        help_text="Example: DSG-001",
    )

    designer_name = models.CharField(
        max_length=255,
        verbose_name="Designer Name",
    )

    brand_name = models.CharField(
        max_length=255,
        verbose_name="Brand",
    )

    # =========================================================
    # OWNER / CONTACT DETAILS
    # =========================================================

    owner_name = models.CharField(
        max_length=255,
        verbose_name="Owner Name",
    )

    email = models.EmailField(
        verbose_name="Contact Email",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Contact Phone",
    )

    # =========================================================
    # LOCATION
    # =========================================================

    city = models.CharField(
        max_length=100,
        verbose_name="City",
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="State",
    )

    country = models.CharField(
        max_length=100,
        default="India",
        verbose_name="Country",
    )

    # =========================================================
    # DESIGNER CATEGORY
    # =========================================================

    primary_category = models.CharField(
        max_length=150,
        verbose_name="Primary Category",
        help_text="Example: Pet Occasion Wear",
    )

    # =========================================================
    # BUSINESS / COMMERCIAL DETAILS
    # =========================================================

    tier = models.CharField(
        max_length=30,
        choices=Tier.choices,
        default=Tier.EMERGING,
        verbose_name="Designer Tier",
    )

    take_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        verbose_name="Take Rate (%)",
        help_text="Platform commission percentage.",
    )

    # =========================================================
    # GST
    # =========================================================

    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        verbose_name="GST Number",
        validators=[
            RegexValidator(
                regex=r"^[0-9A-Z]{15}$",
                message="Enter a valid 15-character GST number.",
            )
        ],
    )

    # =========================================================
    # KYC
    # =========================================================

    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING,
        db_index=True,
        verbose_name="KYC Status",
    )

    kyc_verified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="KYC Verified At",
    )

    # =========================================================
    # CONTRACT
    # =========================================================

    contract_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Contract Start Date",
    )

    contract_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Contract End Date",
    )

    contract_signed = models.BooleanField(
        default=False,
        verbose_name="Contract Signed",
    )

    # =========================================================
    # DESIGNER PIPELINE STATUS
    # =========================================================

    stage = models.CharField(
        max_length=30,
        choices=Stage.choices,
        default=Stage.LEAD,
        db_index=True,
        verbose_name="Pipeline Stage",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Active",
    )

    # =========================================================
    # PROFILE
    # =========================================================

    logo = models.ImageField(
        upload_to="designers/logos/",
        blank=True,
        null=True,
        verbose_name="Brand Logo",
    )

    profile_image = models.ImageField(
        upload_to="designers/profiles/",
        blank=True,
        null=True,
        verbose_name="Profile Image",
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Designer Description",
    )

    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Website",
    )

    # =========================================================
    # SOCIAL MEDIA
    # =========================================================

    instagram_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Instagram URL",
    )

    facebook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Facebook URL",
    )

    # =========================================================
    # AUDIT FIELDS
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:
        db_table = "designer"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["designer_code"]),
            models.Index(fields=["brand_name"]),
            models.Index(fields=["city"]),
            models.Index(fields=["primary_category"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["kyc_status"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["is_active"]),
        ]

        verbose_name = "Designer"
        verbose_name_plural = "Designers"

    # =========================================================
    # STRING REPRESENTATION
    # =========================================================

    def __str__(self):
        return f"{self.brand_name} ({self.designer_code})"

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def is_kyc_verified(self):
        return self.kyc_status == self.KYCStatus.VERIFIED

    @property
    def is_live(self):
        return self.stage in [
            self.Stage.LIVE,
            self.Stage.ACTIVE,
        ]

    @property
    def contract_is_active(self):
        from django.utils import timezone

        if not self.contract_end_date:
            return False

        return self.contract_end_date >= timezone.localdate()