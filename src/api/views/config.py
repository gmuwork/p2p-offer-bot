import logging
import typing

import simplejson
from django import http
from django import views

from common import utils as common_utils
from src import enums
from src import exceptions
from src import models
from src.api import schemas as api_schemas
from src.services import config as config_services

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[CONFIG-VIEW]"


class Config(views.View):
    def get(
            self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:
        logger.info("{} Fetching all currency offer configs.".format(_LOG_PREFIX))
        try:
            all_configs = config_services.get_all_currency_configs()
        except Exception as e:
            logger.exception(
                "{} Unexpected exception while fetching all currency configs. Error: {}.".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )

        logger.info("{} Fetched all currency configs.".format(_LOG_PREFIX))
        json_response = [
            self._format_config_response(config=config) for config in all_configs
        ]
        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps({"data": json_response}),
            status=200,
        )

    def post(
            self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:
        try:
            payload = simplejson.loads(request.body.decode("utf-8"))
        except Exception:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        logger.info(
            "{} Received currency config to save (payload={}).".format(
                _LOG_PREFIX, payload
            )
        )

        validated_data = common_utils.validate_data_schema(
            data=payload, schema=api_schemas.Config()
        )
        if not validated_data:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        try:
            config = config_services.set_currency_offer_config(
                currency=enums.CryptoCurrency(validated_data["currency"]),
                offer_provider=enums.OfferProvider[validated_data["provider"]],
                config_name=validated_data["config_name"],
                config_value=validated_data["config_value"],
            )
        except exceptions.CurrencyConfigNotSupportedError as e:
            logger.exception(
                "{} {}.".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps(
                    {
                        "error": {
                            "title": common_utils.get_exception_message(exception=e)
                        }
                    }
                ),
                status=400,
            )
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while saving offer. Error: {}".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )

        logger.info(
            "{} Successfully set currency config (payload={}).".format(
                _LOG_PREFIX, validated_data
            )
        )
        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps(
                {"data": self._format_config_response(config=config)}
            ),
            status=200,
        )

    @staticmethod
    def _format_config_response(config: models.CurrencyConfig) -> typing.Dict:
        return {
            "id": config.id,
            "attributes": {
                "currency": config.currency,
                "provider": config.provider_name,
                "name": config.name,
                "value": config.value,
            },
        }
