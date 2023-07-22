import dataclasses
import datetime
import decimal
import typing

from src import enums


@dataclasses.dataclass
class AuthenticationToken:
    token: str
    expires_at: datetime.datetime


@dataclasses.dataclass
class Offer:
    offer_id: str
    currency: enums.CryptoCurrency
    conversion_currency: enums.FiatCurrency
    price: decimal.Decimal
    type: enums.OfferType
    payment_method: enums.PaymentMethod
    owner_last_seen_timestamp: typing.Optional[decimal.Decimal]
