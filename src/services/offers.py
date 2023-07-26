import logging
import typing

from src import enums
from src import models
from src.integrations.providers import factory as provider_factory

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[OFFER-SERVICE]"


def fetch_and_save_offer(
        offer_id: str,
        offer_provider: enums.OfferProvider,
        offer_owner_type: enums.OfferOwnerType,
        override_existing_offer_type: bool = False,
) -> typing.Optional[models.Offer]:
    logger.info(
        "{} Fetching offer (id={}) from provider (provider_name={}).".format(
            _LOG_PREFIX, offer_id, offer_provider.name
        )
    )

    provider_client = provider_factory.ProviderFactory().create(provider=offer_provider)
    offer = provider_client.get_offer(offer_id=offer_id)
    logger.info(
        "{} Fetched offer (id={}) from provider. Saving to DB.".format(
            _LOG_PREFIX, offer_id
        )
    )
    offer_db = (
        models.Offer.objects.filter(offer_id=offer_id, provider=offer_provider.value)
        .order_by("id")
        .last()
    )
    if offer_db:
        logger.info(
            "{} Offer (id={}) is already present in db.".format(_LOG_PREFIX, offer_id)
        )

        if override_existing_offer_type:
            logger.info(
                "{} Changing offer (id={}) owner type to (offer_owner_type={}).".format(
                    _LOG_PREFIX, offer_id, offer_owner_type.name
                )
            )
            offer_db.owner_type = offer_owner_type.value
            offer_db.owner_type_name = offer_owner_type.name
            offer_db.save(update_fields=["owner_type", "owner_type_name", "updated_at"])

        return

    saved_offer = models.Offer.objects.create(
        offer_id=offer.offer_id,
        owner_type=offer_owner_type.value,
        owner_type_name=offer_owner_type.name,
        status=enums.OfferStatus.ACTIVE.value,
        status_name=enums.OfferStatus.ACTIVE.name,
        offer_type=offer.type.value,
        offer_type_name=offer.type.name,
        currency=offer.currency.name,
        conversion_currency=offer.conversion_currency.name,
        payment_method=offer.payment_method.value if offer.payment_method else None,
        provider=offer_provider.value,
        provider_name=offer_provider.name,
    )

    logger.info(
        "{} Saved offer (id={}, provider_name={}).".format(
            _LOG_PREFIX, saved_offer.id, offer_provider.name
        )
    )

    return saved_offer


def get_all_offers(
        offer_owner_type: enums.OfferOwnerType
) -> typing.List[models.Offer]:
    return models.Offer.objects.filter(
        owner_type=offer_owner_type.value
    )


def change_offer_status(offer_id: str, offer_status: str) -> models.Offer:
    logger.info(
        "{} Changing offer status (offer_id={}, offer_status={}).".format(
            _LOG_PREFIX, offer_id, offer_status
        )
    )
    offer_status = enums.OfferStatus.convert_from_status(status=offer_status)

    offer = models.Offer.objects.get(offer_id=offer_id)
    offer.status = offer_status.value
    offer.status_name = offer_status.name
    offer.save(update_fields=["status", "updated_at"])

    logger.info(
        "{} Changed offer status (offer_id={}, offer_status={}).".format(
            _LOG_PREFIX, offer_id, offer_status
        )
    )
    return offer
