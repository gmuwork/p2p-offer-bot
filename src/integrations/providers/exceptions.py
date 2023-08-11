class AuthenticationProviderError(Exception):
    pass


class AuthenticationProviderClientError(AuthenticationProviderError):
    pass


class AuthenticationProviderDataValidationError(AuthenticationProviderError):
    pass


class AuthenticationProviderNotSupportedError(AuthenticationProviderError):
    pass


class ProviderError(Exception):
    pass


class ProviderClientError(ProviderError):
    pass


class ProviderDataValidationError(ProviderError):
    pass


class ProviderNotSupportedError(ProviderError):
    pass
