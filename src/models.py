from django.db import models as django_db_models


class AuthenticationToken(django_db_models.Model):
    token = django_db_models.TextField(null=False)
    expire_at = django_db_models.DateTimeField(null=False)
    status = django_db_models.SmallIntegerField(null=False)
    status_name = django_db_models.CharField(max_length=255, null=False)
    provider = django_db_models.SmallIntegerField(null=True)
    provider_name = django_db_models.CharField(max_length=255, null=True)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_authentication_token"


class Offer(django_db_models.Model):
    offer_id = django_db_models.CharField(max_length=255, null=False, unique=True)
    owner_type = django_db_models.PositiveSmallIntegerField(null=False)
    owner_type_name = django_db_models.CharField(max_length=255, null=False)
    status = django_db_models.PositiveSmallIntegerField(null=False)
    status_name = django_db_models.CharField(max_length=255, null=False)
    offer_type = django_db_models.CharField(max_length=255, null=False)
    offer_type_name = django_db_models.CharField(max_length=255, null=False)
    currency = django_db_models.CharField(max_length=5, null=False)
    conversion_currency = django_db_models.CharField(max_length=5, null=False)
    payment_method = django_db_models.CharField(max_length=255, null=False)
    provider = django_db_models.SmallIntegerField(null=True)
    provider_name = django_db_models.CharField(max_length=255, null=True)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_offer"
        indexes = [
            django_db_models.Index(fields=["status", "owner_type"]),
        ]


class OfferHistory(django_db_models.Model):
    offer = django_db_models.ForeignKey(
        Offer, on_delete=django_db_models.PROTECT, related_name="internal_offer"
    )
    competitor_offer = django_db_models.ForeignKey(
        Offer, on_delete=django_db_models.PROTECT, related_name="competitor_offer"
    )
    original_offer_price = django_db_models.DecimalField(
        max_digits=28, decimal_places=8
    )
    updated_offer_price = django_db_models.DecimalField(max_digits=28, decimal_places=8)
    competitor_offer_price = django_db_models.DecimalField(
        max_digits=28, decimal_places=8
    )
    provider = django_db_models.SmallIntegerField(null=True)
    provider_name = django_db_models.CharField(max_length=255, null=True)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_offer_history"


class CurrencyConfig(django_db_models.Model):
    currency = django_db_models.CharField(max_length=255, null=False)
    name = django_db_models.CharField(max_length=255, null=False)
    value = django_db_models.CharField(max_length=255, null=False)
    provider = django_db_models.SmallIntegerField(null=True)
    provider_name = django_db_models.CharField(max_length=255, null=True)

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_currency_config"
        unique_together = ["currency", "name", "provider"]
