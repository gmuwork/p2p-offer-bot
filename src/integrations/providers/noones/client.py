import datetime
import decimal
import logging
import typing

from common import utils as common_utils
from src import enums
from src.integrations.gateways.noones import client as noones_client
from src.integrations.gateways.noones import exceptions as noones_client_exceptions
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
        return noones_client.NoonesAuthAPIClient

    def create_authentication_token(self) -> provider_mesages.AuthenticationToken:
        try:
            response = self.get_rest_api_client().create_authentication_token()
        except noones_client_exceptions.NoonesAuthAPIException as e:
            msg = "Unable to create authentication token through provider API client. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.AuthenticationProviderClientError(msg)

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


class NoonesProvider(base_provider.BaseProvider):
    _LOG_PREFIX = "[NOONES-PROVIDER]"

    def __init__(self) -> None:
        super(NoonesProvider, self).__init__()

    @property
    def provider(self) -> enums.OfferProvider:
        return enums.OfferProvider.NOONES

    @property
    def provider_api_client_class(self) -> typing.Callable:
        return noones_client.NoonesApiClient

    def get_offer(self, offer_id: str) -> messages.Offer:
        try:
            response = self.get_rest_api_client().get_offer(offer_id=offer_id)
        except noones_client_exceptions.NoonesAPIException as e:
            msg = "Exception occurred while getting offer (offer_id={}). Error: {}".format(
                offer_id, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.ProviderClientError(msg)

        validated_offer = common_utils.validate_data_schema(
            data=response, schema=schemas.Offer()
        )
        if not validated_offer:
            msg = "Offer (offer_id={}) response data is not valid (raw_response_data={})".format(
                offer_id, response
            )
            logger.error("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.ProviderDataValidationError(msg)

        return self._construct_offer_data(data=validated_offer)

    def get_all_offers(
            self,
            offer_type: enums.OfferType,
            currency: enums.CryptoCurrency,
            conversion_currency: enums.FiatCurrency,
            payment_method: enums.PaymentMethod,
            min_price: decimal.Decimal,
            max_price: decimal.Decimal,
    ) -> typing.List[messages.Offer]:
        pass

    def update_offer_price(self, offer_id: str, price: decimal.Decimal) -> bool:
        pass

    @staticmethod
    def _construct_offer_data(data: typing.Dict) -> messages.Offer:
        return messages.Offer(
            offer_id=data["offer_id"],
            type=enums.OfferType(data["offer_type"]),
            currency=enums.CryptoCurrency(data["crypto_currency_code"]),
            conversion_currency=enums.FiatCurrency(data["fiat_currency_code"]),
            price=data["fiat_price_per_crypto"],
            payment_method=enums.PaymentMethod(data["payment_method_slug"]),
            owner_last_seen_timestamp=data["last_seen_timestamp"],
        )
