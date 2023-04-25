import enum


class CryptoCurrency(enum.Enum):
    BTC = "BTC"
    USDT = "USDT"


class FiatCurrency(enum.Enum):
    USD = "USD"
    ZAR = "ZAR"


class AuthenticationTokenStatus(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2


class OfferType(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class PaymentMethod(enum.Enum):
    BANK_TRANSFER = "bank-transfer"


class UserCountry(enum.Enum):
    ALL = "WORLDWIDE"


class OfferOwnerType(enum.Enum):
    INTERNAL = 1
    COMPETITOR = 2
