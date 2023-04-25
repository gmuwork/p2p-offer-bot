import logging
import typing

from django.core.management.base import BaseCommand

from common import utils as common_utils
from src.services import authentication as authentication_services

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Maintains active authentication pool.
            ex. python manage.py maintain_active_auth_token 
            """

    log_prefix = "[MAINTAIN-ACTIVE-AUTH-TOKEN]"

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        logger.info(
            "{} Started command '{}'.".format(
                self.log_prefix,
                __name__.split(".")[-1],
            )
        )

        try:
            authentication_services.maintain_active_authentication_token()
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while maintaining active authentication token. Error: {}.".format(
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
