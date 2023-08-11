import datetime
import logging

from django.core.cache import cache

from src import constants
from src import enums
from src import models
from src.integrations.providers import base as base_provider

logger = logging.getLogger(__name__)


class AuthenticationService(object):
    def __init__(
        self, provider_client: base_provider.BaseAuthenticationProvider
    ) -> None:
        self._provider_client = provider_client
        self._log_prefix = "[{}-AUTHENTICATION-SERVICE]".format(
            self._provider_client.provider.name
        )

    def create_authentication_token(self) -> None:
        logger.info(
            "{} Started creating authentication token.".format(self._log_prefix)
        )
        api_authentication_token = self._provider_client.create_authentication_token()
        logger.info(
            "{} Created authentication token (token={}).".format(
                self._log_prefix, api_authentication_token.token
            )
        )

        db_authentication_token = models.AuthenticationToken.objects.create(
            token=api_authentication_token.token,
            expire_at=api_authentication_token.expires_at,
            status=enums.AuthenticationTokenStatus.ACTIVE.value,
            status_name=enums.AuthenticationTokenStatus.ACTIVE.name,
            provider=self._provider_client.provider.value,
            provider_name=self._provider_client.provider.name,
        )
        logger.info(
            "{} Saved authentication token (token_id={}).".format(
                self._log_prefix, db_authentication_token.id
            )
        )

        cache.set(
            key=constants.AUTHENTICATION_TOKEN_CACHE_KEY.format(
                provider=self._provider_client.provider.name
            ),
            value=db_authentication_token.token,
            timeout=constants.CACHE_MAX_TTL,
        )
        logger.info("{} Saved authentication token to cache.".format(self._log_prefix))

    def deactivate_authentication_token(self, token_id: int) -> None:
        logger.info(
            "{} Deactivating authentication token (token_id={}).".format(
                self._log_prefix, token_id
            )
        )

        models.AuthenticationToken.objects.filter(id=token_id).update(
            status=enums.AuthenticationTokenStatus.INACTIVE.value,
            status_name=enums.AuthenticationTokenStatus.INACTIVE.name,
            updated_at=datetime.datetime.now(),
        )

        logger.info(
            "{} Deactivated authentication token (token_id={}).".format(
                self._log_prefix, token_id
            )
        )

    def maintain_active_authentication_token(self) -> None:
        db_token = (
            models.AuthenticationToken.objects.filter(
                status=enums.AuthenticationTokenStatus.ACTIVE.value,
                provider=self._provider_client.provider.value,
            )
            .order_by("id")
            .last()
        )

        if not db_token:
            self.create_authentication_token()
            return

        token_expiration_date = db_token.expire_at - datetime.timedelta(
            hours=constants.AUTHENTICATION_TOKEN_VALIDITY_TIMEDELTA_HRS
        )
        if datetime.datetime.now(datetime.timezone.utc) > token_expiration_date:
            self.deactivate_authentication_token(token_id=db_token.id)
            return

        cache.set(
            key=constants.AUTHENTICATION_TOKEN_CACHE_KEY.format(
                provider=self._provider_client.provider.name
            ),
            value=db_token.token,
            timeout=constants.CACHE_MAX_TTL,
        )
        logger.info(
            "{} Authentication token (token_id={}) is active. Updated cache.".format(
                self._log_prefix, db_token.id
            )
        )
