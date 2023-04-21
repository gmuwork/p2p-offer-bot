class NoonesAuthenticationException(Exception):
    pass


class NoonesAuthClientError(NoonesAuthenticationException):
    pass


class NoonesNoActiveAuthenticationTokenError(NoonesAuthenticationException):
    pass
