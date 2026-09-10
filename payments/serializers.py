from rest_framework import serializers


class PaymentInitiateSerializer(serializers.Serializer):

    orderId = serializers.CharField(
        required=True
    )

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True
    )

    currency = serializers.CharField(
        required=True,
        max_length=10
    )

    gateway = serializers.ChoiceField(
        choices=["razorpay", "stripe", "cod"],
        required=True
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value

    def validate_currency(self, value):
        return value.upper()


class PaymentVerifySerializer(serializers.Serializer):

    orderId = serializers.CharField(
        required=True
    )

    paymentId = serializers.CharField(
        required=True
    )

    signature = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )