import datetime
import decimal
import logging
import typing

from django.conf import settings
from django.core.cache import cache

from common import utils as common_utils
from src import constants
from src import enums
from src import exceptions
from src import messages
from src import models
from src.clients.cmc import client as cmc_api_client
from src.clients.cmc import exceptions as cmc_api_exceptions
from src.clients.noones import client as noones_api_client
from src.clients.noones import exceptions as noones_api_exceptions

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[OFFERS]"


def fetch_and_save_offer(offer_id: str, offer_owner_type: enums.OfferOwnerType) -> None:
    logger.info(
        "{} Fetching offer (id={}) from provider.".format(_LOG_PREFIX, offer_id)
    )
    offer = _fetch_offer_from_client(offer_id=offer_id)
    logger.info(
        "{} Fetched offer (id={}) from provider. Saving to DB.".format(
            _LOG_PREFIX, offer_id
        )
    )
    if models.Offer.objects.filter(offer_id=offer["offer_id"]).exists():
        logger.info(
            "{} Offer (id={}) is already present in db. Exiting.".format(
                _LOG_PREFIX, offer_id
            )
        )
        return

    offer_type = enums.OfferType(offer["offer_type"])
    saved_offer = models.Offer.objects.create(
        offer_id=offer["offer_id"],
        owner_type=offer_owner_type.value,
        owner_type_name=offer_owner_type.name,
        status=enums.OfferStatus.ACTIVE.value,
        status_name=enums.OfferStatus.ACTIVE.name,
        offer_type=offer_type.value,
        offer_type_name=offer_type.name,
        currency=enums.CryptoCurrency(offer["crypto_currency_code"]).name,
        conversion_currency=enums.FiatCurrency(offer["fiat_currency_code"]).name,
        payment_method=enums.PaymentMethod(offer["payment_method_slug"]).value,
    )

    logger.info("{} Saved offer (id={}).".format(_LOG_PREFIX, saved_offer.id))


def improve_offer(
        offer_id: str,
        competitive_offer_search_params: messages.OfferSearchParameters,
):
    logger.info(
        "{} Started improving offer (offer_id={}, competitive_offer_search_terms={}).".format(
            _LOG_PREFIX, offer_id, competitive_offer_search_params
        )
    )

    original_offer = _fetch_offer_from_client(offer_id=offer_id)
    competitor_offer = _get_best_competitor_offer(
        internal_offer=original_offer,
        competitive_offer_search_params=competitive_offer_search_params,
    )
    if not competitor_offer:
        logger.error("{} Competitor offer not found. Exiting.".format(_LOG_PREFIX))
        return

    offer_price_to_update = decimal.Decimal(
        competitor_offer["fiat_price_per_crypto"]
    ) + decimal.Decimal(
        settings.CURRENCY_OFFER_CONFIG[competitor_offer["crypto_currency_code"]][
            "amount_to_increase_offer"
        ]
    )

    if (
            decimal.Decimal(original_offer["fiat_price_per_crypto"])
            == offer_price_to_update
    ):
        logger.info(
            "{} Offer (offer_id={}) price {} {} is the same as best competitor offer (offer_id={}). Exiting.".format(
                _LOG_PREFIX,
                offer_id,
                offer_price_to_update,
                original_offer["fiat_currency_code"],
                competitor_offer["offer_id"],
            )
        )
        return

    logger.info(
        "{} Updating offer (offer_id={}) with best competitor offer (offer_id={}) with {} {}.".format(
            _LOG_PREFIX,
            offer_id,
            competitor_offer["offer_id"],
            offer_price_to_update,
            original_offer["fiat_currency_code"],
        )
    )
    try:
        response = noones_api_client.NoonesApiClient().update_offer_price(
            offer_id=offer_id, price_to_update=offer_price_to_update
        )
    except noones_api_exceptions.NoonesAPIException as e:
        msg = "Unexpected exception occurred while updating offer (offer_id={}). Error: {}".format(
            offer_id, common_utils.get_exception_message(exception=e)
        )
        logger.exception("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.NoonesClientError(msg)

    if not response.get("success"):
        logger.error(
            "{} Offer (offer_id={}) is not updated successfully. Exiting.".format(
                _LOG_PREFIX, offer_id
            )
        )
        return

    logger.info(
        "{} Updated offer (offer_id={}) with best competitor offer (offer_id={}) with {} {}.".format(
            _LOG_PREFIX,
            offer_id,
            competitor_offer["offer_id"],
            offer_price_to_update,
            original_offer["fiat_currency_code"],
        )
    )

    _post_process_offer(
        offer=original_offer,
        competitor_offer=competitor_offer,
        updated_price=offer_price_to_update,
    )
    logger.info(
        "{} Finished improving offer (offer_id={}, competitive_offer_search_terms={}).".format(
            _LOG_PREFIX, offer_id, competitive_offer_search_params
        )
    )


def _fetch_offer_from_client(offer_id: str) -> typing.Dict:
    try:
        offer = noones_api_client.NoonesApiClient().get_offer(offer_id=offer_id)
    except noones_api_exceptions.NoonesAPIException as e:
        msg = "Unable to fetch offer (id={}) from provider. Error: {}".format(
            offer_id, common_utils.get_exception_message(exception=e)
        )
        logger.exception("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.NoonesAuthClientError(msg)

    return offer


def _post_process_offer(
        offer: typing.Dict, competitor_offer: typing.Dict, updated_price: decimal.Decimal
) -> None:
    logger.info(
        "{} Started post processing offer (offer_id={}).".format(
            _LOG_PREFIX, offer["offer_id"]
        )
    )

    fetch_and_save_offer(
        offer_id=competitor_offer["offer_id"],
        offer_owner_type=enums.OfferOwnerType.COMPETITOR,
    )
    offer_history = models.OfferHistory.objects.create(
        offer=models.Offer.objects.get(offer_id=offer["offer_id"]),
        competitor_offer=models.Offer.objects.get(
            offer_id=competitor_offer["offer_id"]
        ),
        original_offer_price=decimal.Decimal(offer["fiat_price_per_crypto"]),
        updated_offer_price=updated_price,
        competitor_offer_price=decimal.Decimal(
            competitor_offer["fiat_price_per_crypto"]
        ),
    )
    logger.info(
        "{} Created offer history (offer_id={}, offer_history_id={}).".format(
            _LOG_PREFIX, offer["offer_id"], offer_history.id
        )
    )


def _get_best_competitor_offer(
        internal_offer: typing.Dict,
        competitive_offer_search_params: messages.OfferSearchParameters,
) -> typing.Optional[typing.Dict]:
    crypto_currency = enums.CryptoCurrency(internal_offer["crypto_currency_code"])
    fiat_currency = enums.FiatCurrency(internal_offer["fiat_currency_code"])

    currency_market_price = _get_currency_market_price(
        crypto_currency=crypto_currency, convert_to_fiat_currency=fiat_currency
    )

    search_terms = {
        "offer_type": competitive_offer_search_params.offer_type,
        "crypto_currency": competitive_offer_search_params.currency,
        "conversion_currency": competitive_offer_search_params.conversion_currency,
        "payment_method": competitive_offer_search_params.payment_method,
        "fiat_fixed_price_max": currency_market_price
                                + currency_market_price
                                * (
                                        decimal.Decimal(
                                            settings.CURRENCY_OFFER_CONFIG[crypto_currency.name][
                                                "offer_search_price_upper_margin"
                                            ]
                                        )
                                        / decimal.Decimal("100")
                                ),
        "fiat_fixed_price_min": currency_market_price
                                - currency_market_price
                                * (
                                        decimal.Decimal(
                                            settings.CURRENCY_OFFER_CONFIG[crypto_currency.name][
                                                "offer_search_price_lower_margin"
                                            ]
                                        )
                                        / decimal.Decimal("100")
                                ),
    }

    try:
        offers = noones_api_client.NoonesApiClient().get_all_offers(**search_terms)
    except noones_api_exceptions.NoonesAPIException as e:
        msg = "Unable to fetch relevant offers (crypto_currency={}, convert_to_fiat_currency={}, search_parameters={}). Error: {}".format(
            crypto_currency.name,
            fiat_currency.name,
            competitive_offer_search_params,
            common_utils.get_exception_message(exception=e),
        )
        logger.exception("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.NoonesClientError(msg)

    if not offers:
        logger.info(
            "{} No offers found (crypto_currency={}, convert_to_fiat_currency={}, search_parameters={}).".format(
                _LOG_PREFIX,
                crypto_currency.name,
                fiat_currency.name,
                competitive_offer_search_params,
            )
        )
        return

    relevant_offers = []
    for offer in offers:
        if offer["offer_id"] == internal_offer["offer_id"]:
            continue

        if (
                decimal.Decimal(datetime.datetime.now().timestamp())
                - offer["last_seen_timestamp"]
        ) / 60 > decimal.Decimal(
            settings.CURRENCY_OFFER_CONFIG[crypto_currency.name][
                "offer_owner_last_seen_max_time"
            ]
        ):
            continue

        relevant_offers.append(offer)

    return max(relevant_offers, key=lambda offer: offer["fiat_price_per_crypto"])


def _get_currency_market_price(
        crypto_currency: enums.CryptoCurrency, convert_to_fiat_currency: enums.FiatCurrency
) -> decimal.Decimal:
    market_price = cache.get(
        key=constants.CMC_CURRENCY_MARKET_PRICE_CACHE_KEY.format(
            crypto_currency=crypto_currency.name,
            conversion_fiat_currency=convert_to_fiat_currency.name,
        ),
        default=None,
    )

    if not market_price:
        try:
            market_price_response = (
                cmc_api_client.CoinMarketCapClient().get_market_price(
                    currency=crypto_currency, convert_to=convert_to_fiat_currency
                )
            )
        except cmc_api_exceptions.CoinMarketCapException as e:
            msg = "Unable to get market price (crypto_currency={}, conversion_currency={}). Error: {}.".format(
                crypto_currency.name,
                convert_to_fiat_currency.name,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(_LOG_PREFIX, msg))
            raise exceptions.CMCClientError(msg)

        market_price = market_price_response[crypto_currency.name][0]["quote"][
            convert_to_fiat_currency.name
        ]["price"]
        cache.set(
            key=constants.CMC_CURRENCY_MARKET_PRICE_CACHE_KEY.format(
                crypto_currency=crypto_currency.name,
                conversion_fiat_currency=convert_to_fiat_currency.name,
            ),
            value=market_price,
            timeout=constants.CMC_CURRENCY_MARKET_PRICE_CACHE_TTL,
        )

    return market_price
