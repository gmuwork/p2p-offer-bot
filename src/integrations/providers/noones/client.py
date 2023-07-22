import datetime
import logging
import typing

from common import utils as common_utils
from src import enums
from src.integrations.gateways.noones import client as noones_auth_client
from src.integrations.providers import base as base_provider, messages
from src.integrations.providers import messages as provider_mesages
from src.integrations.providers import exceptions as provider_exceptions
from src.integrations.providers.noones import schemas

logger = logging.getLogger(__name__)


class NoonesAuthenticationProvider(base_provider.BaseAuthenticationProvider):
    _LOG_PREFIX = "[NOONES-AUTHENTICATION-PROVIDER]"

    def __init__(self) -> None:
        super(NoonesAuthenticationProvider, self).__init__()

    @property
    def provider(self) -> enums.OfferProvider:
        return enums.OfferProvider.NOONES

    @property
    def provider_api_client_class(self) -> typing.Callable:
        return noones_auth_client.NoonesAuthAPIClient

    def create_authentication_token(self) -> provider_mesages.AuthenticationToken:
        try:
            response = self.get_rest_api_client().create_authentication_token()
        except Exception:
            raise provider_exceptions.AuthenticationProviderClientError()

        validated_data = common_utils.validate_data_schema(
            data=response, schema=schemas.AuthenticationToken()
        )
        if not validated_data:
            msg = "Authentication token data is not valid"
            logger.error("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.AuthenticationProviderDataValidationError(msg)

        return provider_mesages.AuthenticationToken(
            token=validated_data["access_token"],
            expires_at=datetime.datetime.now()
                       + datetime.timedelta(seconds=validated_data["expires_in"]),
        )
