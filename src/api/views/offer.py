import logging
import typing

import simplejson
from django import http
from django import views

from common import utils as common_utils
from src import enums
from src import models
from src.api import schemas as api_schemas
from src.services import offers as offer_services

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[OFFER-VIEW]"


class Offer(views.View):
    def get(
        self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:
        logger.info("{} Fetching all internal offers.".format(_LOG_PREFIX))
        try:
            all_offers = offer_services.get_all_offers(
                offer_owner_type=enums.OfferOwnerType.INTERNAL
            )
        except Exception as e:
            logger.exception(
                "{} Unexpected exception while fetching all internal offers. Error: {}.".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )
        logger.info("{} Fetched all internal offers.".format(_LOG_PREFIX))
        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps(
                {
                    "data": [
                        self._format_offer_response(offer=offer) for offer in all_offers
                    ]
                }
            ),
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
            "{} Received offer to save (payload={}).".format(_LOG_PREFIX, payload)
        )

        validated_data = common_utils.validate_data_schema(
            data=payload, schema=api_schemas.Offer()
        )
        if not validated_data:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        try:
            offer = offer_services.fetch_and_save_offer(
                offer_id=validated_data["offer_id"],
                offer_provider=enums.OfferProvider[validated_data["provider"]],
                offer_owner_type=enums.OfferOwnerType.INTERNAL,
                override_existing_offer_type=True,
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

        if not offer:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Offer already exists"}}),
                status=409,
            )

        logger.info(
            "{} Successfully processed and saved offer (payload={}).".format(
                _LOG_PREFIX, validated_data
            )
        )
        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps({"data": {"attributes": payload}}),
            status=201,
        )

    def patch(
        self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:

        offer_id = kwargs.get("offer_id")
        if not offer_id:
            logger.error("{} Offer id is not set in path param.")
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps(
                    {"error": {"title": "Request path improperly configured"}}
                ),
                status=400,
            )

        try:
            payload = simplejson.loads(request.body.decode("utf-8"))
        except Exception:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        logger.info(
            "{} Received offer to update (offer_id={}, payload={}).".format(
                _LOG_PREFIX, offer_id, payload
            )
        )

        validated_data = common_utils.validate_data_schema(
            data=payload, schema=api_schemas.PatchOffer()
        )
        if not validated_data:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        try:
            offer = offer_services.change_offer_status(
                offer_id=offer_id,
                offer_status=validated_data["status"],
            )
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while patching offer. Error: {}".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )

        logger.info(
            "{} Updated offer (offer_id={}, payload={}).".format(
                _LOG_PREFIX, offer_id, payload
            )
        )

        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps(
                {"data": self._format_offer_response(offer=offer)}
            ),
            status=200,
        )

    @staticmethod
    def _format_offer_response(offer: models.Offer) -> typing.Dict:
        return {
            "id": offer.id,
            "attributes": {
                "offer_id": offer.offer_id,
                "provider": offer.provider_name,
                "status": offer.status_name,
                "type": offer.offer_type_name,
                "currency": offer.currency,
                "fiat_currency": offer.conversion_currency,
                "payment_method": offer.payment_method,
            },
        }
