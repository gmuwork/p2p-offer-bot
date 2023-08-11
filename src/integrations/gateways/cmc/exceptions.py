class CoinMarketCapException(Exception):
    pass


class BadResponseCodeError(CoinMarketCapException):
    def __init__(self, message: str, code: int) -> None:
        CoinMarketCapException.__init__(self)
        self.message = message
        self.code = code