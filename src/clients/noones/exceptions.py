class NoonesAuthAPIException(Exception):
    pass


class NoonesAuthAPIBadResponseCodeError(NoonesAuthAPIException):
    def __init__(self, message: str, code: int) -> None:
        NoonesAuthAPIException.__init__(self)
        self.message = message
        self.code = code


class NoonesAPIException(Exception):
    pass


class NoonesAPIBadResponseCodeError(NoonesAPIException):
    def __init__(self, message: str, code: int) -> None:
        NoonesAPIException.__init__(self)
        self.message = message
        self.code = code
