from dataclasses import dataclass

from src import enums


@dataclass
class OfferSearchParameters:
    offer_type: enums.OfferType
    currency: enums.CryptoCurrency
    conversion_currency: enums.FiatCurrency
    payment_method: enums.PaymentMethod
