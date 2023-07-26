import datetime
import decimal
import logging
import typing

from common import utils as common_utils
from src import enums
from src.integrations.gateways.paxful import client as paxful_client
from src.integrations.gateways.paxful import exceptions as paxful_client_exceptions
from src.integrations.providers import base as base_provider
from src.integrations.providers import messages as provider_mesages
from src.integrations.providers import exceptions as provider_exceptions
from src.integrations.providers.noones import schemas

logger = logging.getLogger(__name__)


class PaxfulAuthenticationProvider(base_provider.BaseAuthenticationProvider):
    _LOG_PREFIX = "[PAXFUL-AUTHENTICATION-PROVIDER]"

    def __init__(self) -> None:
        super(PaxfulAuthenticationProvider, self).__init__()

    @property
    def provider(self) -> enums.OfferProvider:
        return enums.OfferProvider.PAXFUL

    @property
    def provider_api_client_class(self) -> typing.Callable:
        return paxful_client.PaxfulAuthAPIClient

    def create_authentication_token(self) -> provider_mesages.AuthenticationToken:
        try:
            response = self.get_rest_api_client().create_authentication_token()
        except paxful_client_exceptions.PaxfulAuthAPIException as e:
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


class PaxfulProvider(base_provider.BaseProvider):
    _LOG_PREFIX = "[PAXFUL-PROVIDER]"

    def __init__(self) -> None:
        super(PaxfulProvider, self).__init__()

    @property
    def provider(self) -> enums.OfferProvider:
        return enums.OfferProvider.PAXFUL

    @property
    def provider_api_client_class(self) -> typing.Callable:
        return paxful_client.PaxfulApiClient

    def get_offer(self, offer_id: str) -> provider_mesages.Offer:
        try:
            response = self.get_rest_api_client().get_offer(offer_id=offer_id)
        except paxful_client_exceptions.PaxfulAPIException as e:
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
        min_price: decimal.Decimal,
        max_price: decimal.Decimal,
        payment_method: typing.Optional[enums.PaymentMethod] = None,
    ) -> typing.List[provider_mesages.Offer]:
        try:
            response = self.get_rest_api_client().get_all_offers(
                offer_type=offer_type,
                crypto_currency=currency,
                conversion_currency=conversion_currency,
                payment_method=payment_method,
                fiat_fixed_price_min=min_price,
                fiat_fixed_price_max=max_price,
            )
        except paxful_client_exceptions.PaxfulAPIException as e:
            msg = "Exception occurred while getting all offers (offer_type={}, currency={}, conversion_currency={}, payment_method={}, min_price={}, max_price={}). Error: {}".format(
                offer_type.name,
                currency.name,
                conversion_currency.name,
                payment_method.name if payment_method else None,
                min_price,
                max_price,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.ProviderClientError(msg)

        validated_offers = common_utils.validate_data_schema(
            data={"offers": response}, schema=schemas.Offers()
        )
        if not validated_offers:
            msg = "Offers data is not valid"
            logger.error("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.ProviderDataValidationError(msg)

        return [
            self._construct_offer_data(data=offer_data)
            for offer_data in validated_offers["offers"]
        ]

    def update_offer_price(self, offer_id: str, price: decimal.Decimal) -> bool:
        try:
            response = self.get_rest_api_client().update_offer_price(
                offer_id=offer_id, price_to_update=price
            )
        except paxful_client_exceptions.PaxfulAPIException as e:
            msg = "Unable to update offer (offer_id={}, price={})".format(
                offer_id, price
            )
            logger.exception("{} {}.".format(self._LOG_PREFIX, msg))
            raise provider_exceptions.ProviderClientError(msg)

        return response.get("success", False)

    @staticmethod
    def _construct_offer_data(data: typing.Dict) -> provider_mesages.Offer:
        return provider_mesages.Offer(
            offer_id=data["offer_id"],
            type=enums.OfferType(data["offer_type"]),
            currency=enums.CryptoCurrency(data["crypto_currency_code"]),
            conversion_currency=enums.FiatCurrency(data["fiat_currency_code"]),
            price=data["fiat_price_per_crypto"],
            payment_method=enums.PaymentMethod.convert_from_payment_slug(
                slug=data["payment_method_slug"]
            ),
            owner_last_seen_timestamp=data["last_seen_timestamp"],
        )
