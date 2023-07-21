import decimal
import typing

import requests
import logging
import simplejson
from urllib import parse as url_parser

from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src import enums as source_enums
from src.integrations.gateways.cmc import exceptions

logger = logging.getLogger(__name__)


class CoinMarketCapClient(object):
    API_BASE_URL = settings.COIN_MARKET_CAP_API_URL
    API_VERSION = settings.COIN_MARKET_CAP_API_VERSION
    API_SECRET_KEY = settings.COIN_MARKET_CAP_API_KEY
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[COIN-MARKET-CAP-CLIENT]"

    def get_market_price(
            self,
            currency: source_enums.CryptoCurrency,
            convert_to: typing.Optional[source_enums.FiatCurrency] = None,
    ) -> typing.Dict:
        params = {"symbol": currency.value}

        if convert_to:
            params["convert"] = convert_to.value

        return self._get_response_content(
            response=self._request(
                endpoint="cryptocurrency/quotes/latest",
                method=common_enums.HttpMethod.GET,
                params=params,
            )
        )

    @staticmethod
    def _get_response_content(response: requests.Response) -> typing.Dict:
        return simplejson.loads(response.content, parse_float=decimal.Decimal)["data"]

    def _request(
            self,
            endpoint: str,
            method: common_enums.HttpMethod,
            params: typing.Optional[dict] = None,
            payload: typing.Optional[dict] = None,
    ) -> requests.Response:
        url = url_parser.urljoin(
            base=self.API_BASE_URL, url=self.API_VERSION + endpoint
        )  # THIS CAN BE IMPROVED
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
                raise exceptions.BadResponseCodeError(
                    message=msg, code=response.status_code
                )

            self._check_response_content(response=response)
        except requests.exceptions.ConnectTimeout as e:
            msg = "Connect timeout. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.CoinMarketCapException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.CoinMarketCapException(msg)

        return response

    def _check_response_content(self, response: requests.Response) -> None:
        response_content = simplejson.loads(response.content)
        if response_content.get("status", {}).get("error_message"):
            logger.error(
                "{} Invalid API client response. Error: {}. Error code: {}.".format(
                    self.LOG_PREFIX,
                    response_content["status"]["error_message"],
                    response_content["status"]["error_code"],
                )
            )
            raise exceptions.BadResponseCodeError(
                message=response_content["status"]["error_message"],
                code=response_content["status"]["error_code"],
            )

        if not response_content.get("data"):
            msg = "Invalid API client response"
            logger.error("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.CoinMarketCapException(msg)

    @classmethod
    def _get_request_headers(cls) -> typing.Dict:
        return {
            "Content-Type": "application/json",
            "X-CMC_PRO_API_KEY": cls.API_SECRET_KEY,
        }
