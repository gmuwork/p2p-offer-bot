class NoonesAuthException(Exception):
    pass


class BadResponseCodeError(NoonesAuthException):
    def __init__(self, message: str, code: int) -> None:
        NoonesAuthException.__init__(self)
        self.message = message
        self.code = code
