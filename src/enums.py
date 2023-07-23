import enum
import typing


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
    VISA_DEBIT_CREDIT_CARD = "visa-debitcredit-card"
    OTHER_BANK_TRANSFER = "other-bank-transfer"
    DOMESTIC_WIRE_TRANSFER = "domestic-wire-transfer"

    @staticmethod
    def convert_from_payment_slug(slug: str) -> typing.Optional["PaymentMethod"]:
        try:
            payment_method = PaymentMethod[slug]
        except KeyError:
            return None

        return payment_method


class UserCountry(enum.Enum):
    ALL = "WORLDWIDE"


class OfferOwnerType(enum.Enum):
    INTERNAL = 1
    COMPETITOR = 2


class OfferStatus(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2

    @staticmethod
    def convert_from_status(status: str) -> "OfferStatus":
        return {
            "ACTIVE": OfferStatus.ACTIVE,
            "INACTIVE": OfferStatus.INACTIVE,
        }[status]


class OfferProvider(enum.Enum):
    NOONES = 1
    PAXFUL = 2
