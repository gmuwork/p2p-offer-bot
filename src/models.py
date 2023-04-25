from django.db import models as django_db_models


class AuthenticationToken(django_db_models.Model):
    token = django_db_models.TextField(null=False)
    expire_at = django_db_models.DateTimeField(null=False)
    status = django_db_models.SmallIntegerField(null=False)
    status_name = django_db_models.CharField(max_length=255, null=False)

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

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_offer"


class OfferHistory(django_db_models.Model):
    offer = django_db_models.OneToOneField(
        Offer, on_delete=django_db_models.PROTECT, to_fields="owner_offer_id"
    )
    competitor_offer = django_db_models.OneToOneField(
        Offer, on_delete=django_db_models.PROTECT, to_fields="competitor_offer_id"
    )
    original_offer_price = django_db_models.DecimalField()
    updated_offer_price = django_db_models.DecimalField()
    competitor_offer_price = django_db_models.DecimalField()

    created_at = django_db_models.DateTimeField(auto_now_add=True)
    updated_at = django_db_models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "src"
        db_table = "offerbot_offer_history"
