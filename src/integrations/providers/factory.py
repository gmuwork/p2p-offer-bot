import logging
import typing

from src import enums
from src.integrations.providers import exceptions as provider_exceptions
from src.integrations.providers.noones import client as noones_client

logger = logging.getLogger(__name__)


class AuthenticationProviderFactory(object):
    _LOG_PREFIX = "[AUTHENTICATION-PROVIDER-FACTORY]"
    _PROVIDER_IMPLEMENTATION_MAP = {
        enums.OfferProvider.NOONES: noones_client.NoonesAuthenticationProvider
    }

    def create(
        self, provider: enums.OfferProvider
    ) -> typing.Union[noones_client.NoonesAuthenticationProvider]:
        if provider not in self._PROVIDER_IMPLEMENTATION_MAP:
            msg = "Provider {} is not supported".format(provider.name)
            logger.error("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.AuthenticationProviderNotSupportedError(msg)

        return self._PROVIDER_IMPLEMENTATION_MAP[provider]()
