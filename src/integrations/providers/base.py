import abc
import typing

from src import enums
from src.integrations.providers import messages

T = typing.TypeVar("T")


class BaseAuthenticationProvider(object):
    def __init__(self) -> None:
        self._provider_api_client = None

    @property
    @abc.abstractmethod
    def provider(self) -> enums.OfferProvider:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def provider_api_client_class(self) -> typing.Callable:
        raise NotImplementedError

    def get_rest_api_client(self) -> T:
        if not self._provider_api_client:
            self._provider_api_client = self.provider_api_client_class()

        return self._provider_api_client

    @abc.abstractmethod
    def create_authentication_token(self) -> messages.AuthenticationToken:
        raise NotImplementedError
