import logging
import typing

from django.core.management.base import BaseCommand

from common import utils as common_utils
from src.services import offers as offer_services

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Improves all active offers.
            ex. python manage.py improve_active_offers 
            """

    log_prefix = "[IMPROVE-ACTIVE-OFFERS]"

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        logger.info(
            "{} Started command '{}'.".format(
                self.log_prefix,
                __name__.split(".")[-1],
            )
        )

        try:
            offer_services.improve_internal_active_offers()
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while improving all active internal offers. Error: {}.".format(
                    self.log_prefix,
                    common_utils.get_exception_message(exception=e),
                )
            )

        logger.info(
            "{} Finished command '{}'.".format(
                self.log_prefix,
                __name__.split(".")[-1],
            )
        )
