class PaxfulAuthAPIException(Exception):
    pass


class PaxfulAuthAPIBadResponseCodeError(PaxfulAuthAPIException):
    def __init__(self, message: str, code: int) -> None:
        PaxfulAuthAPIException.__init__(self)
        self.message = message
        self.code = code
