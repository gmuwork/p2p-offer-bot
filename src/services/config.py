import datetime
import logging
import typing

from django.core.cache import cache

from src import constants
from src import enums
from src import exceptions
from src import models

logger = logging.getLogger(__name__)
_LOG_PREFIX = "[CONFIG]"


def set_currency_offer_config(
    currency: enums.CryptoCurrency, config_name: str, config_value: str
) -> models.CurrencyConfig:
    logger.info(
        "{} Setting currency offer config (currency={}, config_name={}, config_value={}).".format(
            _LOG_PREFIX, currency.name, config_name, config_value
        )
    )
    if config_name not in constants.CURRENCY_CONFIGS:
        msg = "Currency config name is not one of supported config names"
        logger.error("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.CurrencyConfigNotSupportedError(msg)

    currency_config, _ = models.CurrencyConfig.objects.update_or_create(
        name=config_name,
        currency=currency.value,
        defaults={
            "value": config_value,
            "updated_at": datetime.datetime.now(),
        },
    )
    logger.info(
        "{} Set currency offer config (config_id={}).".format(
            _LOG_PREFIX, currency_config.id
        )
    )
    cache.set(
        key=constants.CURRENCY_CONFIG_CACHE_NAME.format(
            config_name=config_name, currency=currency.name
        ),
        value=config_value,
        timeout=constants.CACHE_MAX_TTL,
    )
    logger.info(
        "{} Currency offer config (config_name={}) set to cache.".format(
            _LOG_PREFIX, config_name
        )
    )
    return currency_config


def get_currency_offer_config(currency: enums.CryptoCurrency, config_name: str) -> str:
    if config_name not in constants.CURRENCY_CONFIGS:
        msg = "Currency config name is not one of supported configs"
        logger.error("{} {}.".format(_LOG_PREFIX, msg))
        raise exceptions.CurrencyConfigNotSupportedError(msg)

    config_value = cache.get(
        key=constants.CURRENCY_CONFIG_CACHE_NAME.format(
            config_name=config_name, currency=currency.name
        ),
        default=None,
    )
    if not config_value:
        config_value = models.CurrencyConfig.objects.get(
            currency=currency.value, name=config_name
        ).value

    if not config_value:
        raise exceptions.CurrencyOfferConfigNotFoundError(
            "Currency offer config not found (currency={}, config_name={})".format(
                currency.name, config_name
            )
        )

    cache.set(
        key=constants.CURRENCY_CONFIG_CACHE_NAME.format(
            config_name=config_name, currency=currency.name
        ),
        value=config_value,
        timeout=constants.CACHE_MAX_TTL,
    )
    return config_value


def get_all_currency_configs() -> typing.List[models.CurrencyConfig]:
    return models.CurrencyConfig.objects.all()
