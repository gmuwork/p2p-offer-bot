class NoonesAuthenticationException(Exception):
    pass


class NoonesAuthClientError(NoonesAuthenticationException):
    pass


class NoonesNoActiveAuthenticationTokenError(NoonesAuthenticationException):
    pass


class NoonesException(Exception):
    pass


class NoonesClientError(NoonesException):
    pass


class CMCException(Exception):
    pass


class CMCClientError(CMCException):
    pass
