import datetime
import decimal
import logging
import typing

from django.conf import settings
from django.core import mail
from django.core.cache import cache

from common import utils as common_utils
from src import constants
from src import enums
from src import exceptions
from src import models
from src.services import config as config_services
from src.integrations.providers import base as base_provider
from src.integrations.providers import messages as provider_messages
from src.integrations.gateways.cmc import (
    client as cmc_api_client,
    exceptions as cmc_api_exceptions,
)

logger = logging.getLogger(__name__)


class OfferImproverService(object):
    def __init__(self, provider_client: base_provider.BaseProvider) -> None:
        self._provider_client = provider_client
        self._log_prefix = "[{}-OFFER-SERVICE]".format(
            self._provider_client.provider.name
        )

    def improve_internal_active_offers(self) -> None:
        logger.info(
            "{} Started improving internal active offers.".format(self._log_prefix)
        )
        internal_active_offers = models.Offer.objects.filter(
            owner_type=enums.OfferOwnerType.INTERNAL.value,
            status=enums.OfferStatus.ACTIVE.value,
            provider=self._provider_client.provider.value,
        )

        if not internal_active_offers:
            logger.info(
                "{} Not found active internal offers to improve. Exiting.".format(
                    self._log_prefix
                )
            )
            return

        logger.info(
            "{} Found {} active internal offers to improve.".format(
                self._log_prefix, internal_active_offers.count()
            )
        )
        for internal_active_offer in internal_active_offers:
            try:
                self.improve_offer(offer_id=internal_active_offer.offer_id)
            except Exception as e:
                msg = "Exception occurred while improving offer (offer_id={}). Error: {}".format(
                    internal_active_offer.offer_id,
                    common_utils.get_exception_message(exception=e),
                )
                logger.exception("{} {}.".format(self._log_prefix, msg))
                mail.send_mail(
                    from_email=settings.EMAIL_HOST_USER,
                    subject="ERROR",
                    message=msg,
                    recipient_list=settings.LOGGING_EMAIL_RECIPIENT_LIST,
                    fail_silently=False,
                )
                continue

        logger.info(
            "{} Finished improving internal active offers.".format(self._log_prefix)
        )

    def improve_offer(
        self,
        offer_id: str,
    ):
        logger.info(
            "{} Started improving offer (offer_id={}).".format(
                self._log_prefix, offer_id
            )
        )
        internal_offer = self._provider_client.get_offer(offer_id=offer_id)
        competitor_offer = self._get_best_competitor_offer(
            internal_offer=internal_offer
        )
        if not competitor_offer:
            logger.error(
                "{} Competitor offer not found. Exiting.".format(self._log_prefix)
            )
            return

        offer_price_to_update = competitor_offer.price + decimal.Decimal(
            config_services.get_currency_offer_config(
                currency=competitor_offer.currency,
                config_name="amount_to_increase_offer",
                offer_provider=self._provider_client.provider,
            )
        )

        if internal_offer.price == offer_price_to_update:
            logger.info(
                "{} Offer (offer_id={}) price {} {} is the same as best competitor offer (offer_id={}). Exiting.".format(
                    self._log_prefix,
                    offer_id,
                    offer_price_to_update,
                    internal_offer.conversion_currency.name,
                    competitor_offer.offer_id,
                )
            )
            return

        logger.info(
            "{} Updating offer (offer_id={}) with best competitor offer (offer_id={}) with {} {}.".format(
                self._log_prefix,
                offer_id,
                competitor_offer.offer_id,
                offer_price_to_update,
                internal_offer.conversion_currency.name,
            )
        )

        updated_offer = self._provider_client.update_offer_price(
            offer_id=offer_id, price=offer_price_to_update
        )
        if not updated_offer:
            logger.error(
                "{} Offer (offer_id={}) is not updated successfully. Exiting.".format(
                    self._log_prefix, offer_id
                )
            )
            return

        logger.info(
            "{} Updated offer (offer_id={}) with best competitor offer (offer_id={}) with {} {}.".format(
                self._log_prefix,
                offer_id,
                competitor_offer.offer_id,
                offer_price_to_update,
                internal_offer.conversion_currency.name,
            )
        )

        self._post_process_offer(
            internal_offer=internal_offer,
            competitor_offer=competitor_offer,
            updated_price=offer_price_to_update,
        )
        logger.info(
            "{} Finished improving offer (offer_id={}).".format(
                self._log_prefix, offer_id
            )
        )

    def _get_best_competitor_offer(
        self,
        internal_offer: provider_messages.Offer,
    ) -> typing.Optional[provider_messages.Offer]:
        currency_market_price = self._get_currency_market_price(
            crypto_currency=internal_offer.currency,
            convert_to_fiat_currency=internal_offer.conversion_currency,
        )

        competitor_offer_max_price = currency_market_price + currency_market_price * (
            decimal.Decimal(
                config_services.get_currency_offer_config(
                    # TODO: This has to be extended to be per provider
                    currency=internal_offer.currency,
                    config_name="search_price_upper_margin",
                    offer_provider=self._provider_client.provider,
                )
            )
            / decimal.Decimal("100")
        )

        competitor_offer_min_price = currency_market_price - currency_market_price * (
            decimal.Decimal(
                config_services.get_currency_offer_config(
                    currency=internal_offer.currency,
                    config_name="search_price_lower_margin",
                    offer_provider=self._provider_client.provider,
                )
            )
            / decimal.Decimal("100")
        )
        competitor_offers = self._provider_client.get_all_offers(
            offer_type=internal_offer.type,
            currency=internal_offer.currency,
            conversion_currency=internal_offer.conversion_currency,
            payment_method=internal_offer.payment_method
            if not settings.OFFER_SEARCH_ALL_BANK_PAYMENT_METHODS
            else None,
            max_price=competitor_offer_max_price,
            min_price=competitor_offer_min_price,
        )
        if not competitor_offers:
            logger.info(
                "{} No competitor offers found (crypto_currency={}, convert_to_fiat_currency={}, offer_type={}, max_price={}, min_price={}).".format(
                    self._log_prefix,
                    internal_offer.currency.name,
                    internal_offer.conversion_currency.name,
                    internal_offer.type.name,
                    competitor_offer_max_price,
                    competitor_offer_min_price,
                )
            )
            return

        relevant_offers_above_market_price = []
        relevant_offers_below_market_price = []
        for offer in competitor_offers:
            if offer.offer_id == internal_offer.offer_id:
                continue

            if (
                decimal.Decimal(datetime.datetime.now().timestamp())
                - offer.owner_last_seen_timestamp
            ) / 60 > decimal.Decimal(
                config_services.get_currency_offer_config(
                    currency=internal_offer.currency,
                    config_name="owner_last_seen_max_time",
                    offer_provider=self._provider_client.provider,
                )
            ):
                continue

            # TEMPORARY UNTIL CONFIRMED WITH CLIENT
            if (
                settings.OFFER_SEARCH_ALL_BANK_PAYMENT_METHODS
                and offer.payment_method
                not in [
                    enums.PaymentMethod.BANK_TRANSFER,
                    enums.PaymentMethod.OTHER_BANK_TRANSFER,
                    enums.PaymentMethod.DOMESTIC_WIRE_TRANSFER,
                ]
            ):
                continue

            if offer.price > currency_market_price:
                relevant_offers_above_market_price.append(offer)
            else:
                relevant_offers_below_market_price.append(offer)

        if relevant_offers_below_market_price:
            return max(
                relevant_offers_below_market_price, key=lambda offer: offer.price
            )

        return min(relevant_offers_above_market_price, key=lambda offer: offer.price)

    def _get_currency_market_price(
        self,
        crypto_currency: enums.CryptoCurrency,
        convert_to_fiat_currency: enums.FiatCurrency,
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
                logger.exception("{} {}.".format(self._log_prefix, msg))
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

    def _post_process_offer(
        self,
        internal_offer: provider_messages.Offer,
        competitor_offer: provider_messages.Offer,
        updated_price: decimal.Decimal,
    ) -> None:
        logger.info(
            "{} Started post processing internal offer (offer_id={}).".format(
                self._log_prefix, internal_offer.offer_id
            )
        )

        if not models.Offer.objects.filter(
            offer_id=competitor_offer.offer_id,
            provider=self._provider_client.provider.value,
        ).exists():
            competitor_offer_db = models.Offer.objects.create(
                offer_id=competitor_offer.offer_id,
                owner_type=enums.OfferOwnerType.COMPETITOR.value,
                owner_type_name=enums.OfferOwnerType.COMPETITOR.name,
                status=enums.OfferStatus.ACTIVE.value,
                status_name=enums.OfferStatus.ACTIVE.name,
                offer_type=competitor_offer.type.value,
                offer_type_name=competitor_offer.type.name,
                currency=competitor_offer.currency.name,
                conversion_currency=competitor_offer.conversion_currency.name,
                payment_method=competitor_offer.payment_method.value,
                provider=self._provider_client.provider.value,
                provider_name=self._provider_client.provider.name,
            )
            logger.info(
                "{} Created competitor offer (id={}).".format(
                    self._log_prefix,
                    competitor_offer_db.id,
                )
            )

        offer_history = models.OfferHistory.objects.create(
            offer=models.Offer.objects.get(
                offer_id=internal_offer.offer_id,
                provider=self._provider_client.provider.value,
            ),
            competitor_offer=models.Offer.objects.get(
                offer_id=competitor_offer.offer_id
            ),
            original_offer_price=internal_offer.price,
            updated_offer_price=updated_price,
            competitor_offer_price=competitor_offer.price,
            provider=self._provider_client.provider.value,
            provider_name=self._provider_client.provider.name,
        )
        logger.info(
            "{} Created offer history (offer_id={}, offer_history_id={}).".format(
                self._log_prefix, internal_offer.offer_id, offer_history.id
            )
        )
