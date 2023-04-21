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