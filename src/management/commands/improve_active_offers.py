import logging
import typing

from django.core.management.base import BaseCommand
from django.core.management.base import CommandParser

from common import utils as common_utils
from src import enums
from src.services import offer_improver as offer_improver_services
from src.integrations.providers import factory as provider_factory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Improves all active offers.
            ex. python manage.py improve_active_offers 
            """

    log_prefix = "[IMPROVE-ACTIVE-OFFERS]"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--provider",
            required=True,
            type=str,
            choices=[offer_provider.name for offer_provider in enums.OfferProvider],
            help="One of offer providers specified in OfferProvider enum.",
        )

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        logger.info(
            "{} Started command '{}' (provider={}).".format(
                self.log_prefix, __name__.split(".")[-1], kwargs["provider"]
            )
        )

        try:
            offer_improver_services.OfferImproverService(
                provider_client=provider_factory.ProviderFactory().create(
                    provider=enums.OfferProvider[kwargs["provider"]]
                )
            ).improve_internal_active_offers()
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while improving all active internal offers. Error: {}.".format(
                    self.log_prefix,
                    common_utils.get_exception_message(exception=e),
                )
            )

        logger.info(
            "{} Finished command '{}' (provider={}).".format(
                self.log_prefix, __name__.split(".")[-1], kwargs["provider"]
            )
        )
