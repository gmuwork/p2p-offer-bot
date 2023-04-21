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
