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
from src.clients.noones import enums
from src.clients.noones import exceptions

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
                raise exceptions.BadResponseCodeError(
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
            raise exceptions.NoonesAuthException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.NoonesAuthException(msg)

        return response

    @classmethod
    def _get_request_headers(cls) -> typing.Dict:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
        }
