import logging
import typing

from django.core.management.base import BaseCommand
from django.core.management.base import CommandParser

from common import utils as common_utils
from src import enums
from src.integrations.providers import factory as provider_factory
from src.services import authentication as authentication_services

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Maintains active authentication token pool.
            ex. python manage.py maintain_active_auth_token  --provider=PAXFUL
            """

    log_prefix = "[MAINTAIN-ACTIVE-AUTH-TOKEN]"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--provider",
            required=True,
            type=str,
            choices=[offer_provider.name for offer_provider in enums.OfferProvider],
            help="One of offer providers specified in OfferProvider enum.",
        )

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        offer_provider = enums.OfferProvider[kwargs["provider"]]
        logger.info(
            "{} Started command '{}' (provider={}).".format(
                self.log_prefix,
                __name__.split(".")[-1],
                offer_provider.name,
            )
        )

        try:
            authentication_services.AuthenticationService(
                provider_client=provider_factory.AuthenticationProviderFactory().create(
                    provider=offer_provider
                )
            ).maintain_active_authentication_token()
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while maintaining active authentication token (provider={}). Error: {}.".format(
                    self.log_prefix,
                    offer_provider.name,
                    common_utils.get_exception_message(exception=e),
                )
            )

        logger.info(
            "{} Finished command '{}' (provider={}).".format(
                self.log_prefix,
                __name__.split(".")[-1],
                offer_provider.name,
            )
        )
