import datetime
import logging

from django.core.cache import cache

from common import utils as common_utils
from src import constants
from src import enums
from src import exceptions
from src import models
from src.clients.noones import client as noones_auth_client
from src.clients.noones import exceptions as noones_auth_client_exceptions

logger = logging.getLogger(__name__)
_LOG_PREFIX = "[NOONES-AUTHENTICATION]"


def create_authentication_token() -> None:
    logger.info("{} Started creating authentication token.".format(_LOG_PREFIX))

    try:
        response = (
            noones_auth_client.NoonesAuthAPIClient().create_authentication_token()
        )
    except noones_auth_client_exceptions.NoonesAuthException as e:
        msg = "Unable to get authentication token from client. Error: {}".format(
            common_utils.get_exception_message(exception=e)
        )
        logger.exception("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.NoonesAuthClientError(msg)

    logger.info(
        "{} Created authentication token (raw_response={}).".format(
            _LOG_PREFIX, response
        )
    )

    authentication_token = models.AuthenticationToken.objects.create(
        token=response["access_token"],
        expire_at=datetime.datetime.now()
        + datetime.timedelta(seconds=response["expires_in"]),
        status=enums.AuthenticationTokenStatus.ACTIVE.value,
        status_name=enums.AuthenticationTokenStatus.ACTIVE.name,
    )
    logger.info(
        "{} Saved authentication token (token_id={}).".format(
            _LOG_PREFIX, authentication_token.id
        )
    )

    cache.set(
        key=constants.NOONES_AUTHENTICATION_TOKEN_CACHE_NAME,
        value=authentication_token.token,
        timeout=constants.CACHE_MAX_TTL,
    )
    logger.info("{} Saved authentication token to cache.".format(_LOG_PREFIX))


def get_authentication_token() -> str:
    cached_token = cache.get(key=constants.NOONES_AUTHENTICATION_TOKEN_CACHE_NAME)
    if cached_token:
        return cached_token

    db_token = (
        models.AuthenticationToken.objects.filter(
            status=enums.AuthenticationTokenStatus.ACTIVE.value,
        )
        .order_by("id")
        .last()
    )

    if db_token:
        return db_token.token

    raise exceptions.NoonesNoActiveAuthenticationTokenError(
        "Authentication token not found neither in cache nor in db"
    )


def deactivate_authentication_token(token_id: int) -> None:
    logger.info(
        "{} Deactivating authentication token (token_id={}).".format(
            _LOG_PREFIX, token_id
        )
    )

    models.AuthenticationToken.objects.filter(id=token_id).update(
        status=enums.AuthenticationTokenStatus.INACTIVE.value,
        status_name=enums.AuthenticationTokenStatus.INACTIVE.name,
        updated_at=datetime.datetime.now(),
    )

    logger.info(
        "{} Deactivated authentication token (token_id={}).".format(
            _LOG_PREFIX, token_id
        )
    )


def maintain_active_authentication_token() -> None:
    logger.info("{} Started activating authentication tokens.".format(_LOG_PREFIX))
    try:
        authentication_token = get_authentication_token()
    except exceptions.NoonesNoActiveAuthenticationTokenError:
        authentication_token = None

    if authentication_token:
        db_authentication_token = (
            models.AuthenticationToken.objects.filter(token=authentication_token)
            .order_by("id")
            .last()
        )

        if not db_authentication_token:
            cache.delete(key=constants.NOONES_AUTHENTICATION_TOKEN_CACHE_NAME)
            msg = "Token {} present in cache and not in the DB. Deleted from cache".format(
                authentication_token
            )
            logger.error("{} {}.".format(_LOG_PREFIX, msg))
            raise exceptions.NoonesNoActiveAuthenticationTokenError(msg)

        if not (
            datetime.datetime.now(datetime.timezone.utc)
            > db_authentication_token.expire_at
            - datetime.timedelta(
                hours=constants.NOONES_AUTHENTICATION_TOKEN_VALIDITY_TIMEDELTA_HRS
            )
        ):
            cache.set(
                key=constants.NOONES_AUTHENTICATION_TOKEN_CACHE_NAME,
                value=db_authentication_token.token,
                timeout=constants.CACHE_MAX_TTL,
            )
            logger.info(
                "{} Authentication token (token_id={}) is active. Updated cache.".format(
                    _LOG_PREFIX, db_authentication_token.id
                )
            )
            return

        deactivate_authentication_token(token_id=db_authentication_token.id)
        logger.info(
            "{} Authentication token (token_id={}) is close to expire. Deactivated.".format(
                _LOG_PREFIX, db_authentication_token.id
            )
        )

    create_authentication_token()
    logger.info("{} Finished activating authentication tokens.".format(_LOG_PREFIX))
