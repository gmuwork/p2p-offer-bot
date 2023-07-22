class AuthenticationProviderError(Exception):
    pass


class AuthenticationProviderClientError(AuthenticationProviderError):
    pass


class AuthenticationProviderDataValidationError(AuthenticationProviderError):
    pass


class AuthenticationProviderNotSupportedError(AuthenticationProviderError):
    pass
