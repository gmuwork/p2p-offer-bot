import logging
import simplejson

from typing import List, Dict, Tuple

from django.conf import settings
from src import enums
from src.clients.noones import client as noones_auth_client
from src.clients.cmc import client as cmc_client

logger = logging.getLogger(__name__)
_LOG_PREFIX = "[NOONES-OFFERS]"


class NoOffersException(Exception):
    def __init__(self, params: Dict) -> None:
        self.message = "No offers with given params found:\n"
        self.message += f"{simplejson.dumps(params)}"


def get_relevant_offers(
    crypto_currency: enums.CryptoCurrency,
    fiat_currency: enums.FiatCurrency,
) -> List[Dict]:
    market_price = cmc_client.CoinMarketCapClient().get_market_price(
        crypto_currency, fiat_currency
    )

    margin_low, margin_high = get_margins(crypto_currency)
    print(margin_low, margin_high, market_price)

    offers = get_latest_offers()
    if not offers:
        raise NoOffersException(
            {
                "crypto_currency": crypto_currency,
                "fiat_currency": fiat_currency,
                "margin_low": margin_low,
                "margin_high": margin_high,
                "market_price": market_price,
            }
        )
    relevant_offers = []
    for offer in offers:
        print(offer)
        # TODO:
        #  - check if price within range
        #  - check when last updated/seen

    return relevant_offers


def get_latest_offers() -> List[Dict]:
    noonesAPI = noones_auth_client.NoonesApiClient()
    return noonesAPI.get_all_offers(
        offer_type=enums.OfferType.SELL,
        crypto_currency=enums.CryptoCurrency.BTC,
        conversion_currency=enums.FiatCurrency.ZAR,
        payment_method=enums.PaymentMethod.BANK_TRANSFER,
    )


def get_margins(
    crypto_currency: enums.CryptoCurrency,
) -> Tuple[int, int]:
    if crypto_currency == enums.CryptoCurrency.BTC:
        low = settings.BTC_MARGIN_LOW
        high = settings.BTC_MARGIN_HIGH
    elif crypto_currency == enums.CryptoCurrency.USDT:
        low = settings.USDT_MARGIN_LOW
        high = settings.USDT_MARGIN_HIGH
    else:
        raise Exception("Unknown crypto currency provided")
    return low, high
