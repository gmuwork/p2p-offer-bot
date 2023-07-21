import decimal
import typing

import requests
import logging
import simplejson
from urllib import parse as url_parser

from django.core.cache import cache
from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src import constants as source_constants
from src import enums as source_enums
from src.integrations.gateways.noones import enums
from src.integrations.gateways.noones import exceptions

logger = logging.getLogger(__name__)


class NoonesAuthAPIClient(object):
    API_BASE_URL = settings.NOONES_AUTH_API_URL
    API_CLIENT_ID = settings.NOONES_AUTH_CLIENT_ID
    API_CLIENT_SECRET = settings.NOONES_AUTH_CLIENT_SECRET
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[NOONES-AUTH-CLIENT]"

    def create_authentication_token(self) -> typing.Dict:
        return simplejson.loads(
            self._request(
                endpoint="oauth2/token",
                method=common_enums.HttpMethod.POST,
                payload={
                    "grant_type": enums.AuthenticationGrantType.CLIENT_CREDENTIALS.value,
                    "client_id": self.API_CLIENT_ID,
                    "client_secret": self.API_CLIENT_SECRET,
                },
            ).content,
            parse_float=decimal.Decimal,
        )

    def _request(
            self,
            endpoint: str,
            method: common_enums.HttpMethod,
            params: typing.Optional[dict] = None,
            payload: typing.Optional[dict] = None,
    ) -> requests.Response:
        url = url_parser.urljoin(base=self.API_BASE_URL, url=endpoint)
        try:
            response = requests.request(
                url=url,
                method=method.value,
                params=params,
                data=payload,
                headers=self._get_request_headers(),
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.NoonesAuthAPIBadResponseCodeError(
                    message=msg, code=response.status_code
                )

            logger.debug(
                "{} Successful response (endpoint={}, status_code={}, payload={}, params={}, raw_response={}).".format(
                    self.LOG_PREFIX,
                    endpoint,
                    response.status_code,
                    payload,
                    params,
                    response.content.decode(encoding="utf-8"),
                )
            )
        except requests.exceptions.ConnectTimeout as e:
            msg = "Connect timeout. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAuthAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAuthAPIException(msg)

        return response

    @classmethod
    def _get_request_headers(cls) -> typing.Dict:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
        }


class NoonesApiClient(object):
    API_BASE_URL = settings.NOONES_API_URL
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[NOONES-API-CLIENT]"

    def get_offer(self, offer_id: str) -> typing.Dict:
        return self._get_response_content(
            response=self._request(
                endpoint="noones/v1/offer/get",
                method=common_enums.HttpMethod.POST,
                payload={
                    "offer_hash": offer_id,
                },
            )
        )

    def get_all_offers(
            self,
            offer_type: source_enums.OfferType,
            crypto_currency: source_enums.CryptoCurrency,
            conversion_currency: source_enums.FiatCurrency = source_enums.FiatCurrency.USD,
            user_country: source_enums.UserCountry = source_enums.UserCountry.ALL,
            payment_method: typing.Optional[source_enums.PaymentMethod] = None,
            fiat_fixed_price_min: typing.Optional[decimal.Decimal] = None,
            fiat_fixed_price_max: typing.Optional[decimal.Decimal] = None,
    ) -> typing.List[typing.Dict]:
        payload = {
            "type": offer_type.value,
            "currency_code": conversion_currency.value,
            "crypto_currency_code": crypto_currency.value,
            "user_country": user_country.value,
        }

        if payment_method:
            payload["payment_method"] = payment_method.value

        if fiat_fixed_price_max:
            payload["fiat_fixed_price_max"] = fiat_fixed_price_max

        if fiat_fixed_price_min:
            payload["fiat_fixed_price_min"] = fiat_fixed_price_min

        return self._get_paginated_response(
            endpoint="noones/v1/offer/all",
            method=common_enums.HttpMethod.POST,
            payload=payload,
            data_field="offers",
        )

    def update_offer_price(
            self, offer_id: str, price_to_update: decimal.Decimal
    ) -> typing.Dict:
        return self._get_response_content(
            response=self._request(
                endpoint="noones/v1/offer/update-price",
                method=common_enums.HttpMethod.POST,
                payload={"offer_hash": offer_id, "fixed_price": price_to_update},
            )
        )

    def _request(
            self,
            endpoint: str,
            method: common_enums.HttpMethod,
            params: typing.Optional[dict] = None,
            payload: typing.Optional[dict] = None,
    ) -> requests.Response:
        url = url_parser.urljoin(base=self.API_BASE_URL, url=endpoint)
        try:
            response = requests.request(
                url=url,
                method=method.value,
                params=params,
                data=payload,
                headers=self._get_request_headers(),
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.NoonesAPIBadResponseCodeError(
                    message=msg, code=response.status_code
                )

            self._check_response(response=response)
            logger.debug(
                "{} Successful response (endpoint={}, status_code={}, payload={}, params={}, raw_response={}).".format(
                    self.LOG_PREFIX,
                    endpoint,
                    response.status_code,
                    payload,
                    params,
                    response.content.decode(encoding="utf-8"),
                )
            )
        except requests.exceptions.ConnectTimeout as e:
            msg = "Connect timeout. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAPIException(msg)

        return response

    @staticmethod
    def _get_response_content(response: requests.Response) -> typing.Dict:
        return simplejson.loads(
            response.content,
            parse_float=decimal.Decimal,
        )["data"]

    def _get_paginated_response(
            self,
            endpoint: str,
            method: common_enums.HttpMethod,
            payload: typing.Dict,
            data_field: str,
            limit: int = 300,
    ) -> typing.List:
        payload.update({"limit": limit, "offset": 0})
        offers = []
        while True:
            data = self._get_response_content(
                response=self._request(
                    endpoint=endpoint,
                    method=method,
                    payload=payload,
                )
            )
            offers.extend(data[data_field])
            payload["offset"] += limit

            if not data["count"]:
                break

        return offers

    def _check_response(self, response: requests.Response) -> None:
        response_content = simplejson.loads(response.content)
        if response_content["status"] != enums.NoonesAPIStatus.SUCCESS.value:
            msg = "Response content error (response_content={}, error_message={}, error_code={})".format(
                response_content,
                response_content.get("error", {}).get("message"),
                response_content.get("error", {}).get("code"),
            )
            logger.error("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAPIBadResponseCodeError(
                message=response_content.get("error", {}).get("message"),
                code=response_content.get("error", {}).get("code"),
            )

        if "data" not in response_content:
            msg = "Invalid response content (response_content={})".format(
                response_content
            )
            logger.error("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAPIException(msg)

    @classmethod
    def _get_request_headers(cls) -> typing.Dict:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer {}".format(
                cache.get(key=source_constants.NOONES_AUTHENTICATION_TOKEN_CACHE_KEY)
            ),
        }
