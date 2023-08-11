import enum


class AuthenticationGrantType(enum.Enum):
    CLIENT_CREDENTIALS = "client_credentials"


class PaxfulAPIStatus(enum.Enum):
    ERROR = "error"
    SUCCESS = "success"
