import enum


class AuthenticationGrantType(enum.Enum):
    CLIENT_CREDENTIALS = "client_credentials"


class NoonesAPIStatus(enum.Enum):
    ERROR = "error"
    SUCCESS = "success"
