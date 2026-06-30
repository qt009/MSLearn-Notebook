import os
from abc import abstractmethod
from typing import Protocol, Type, cast

from azure.identity.aio import DefaultAzureCredential

class MetaConfig(type):
    def _get_config_class(cls) -> Type["ConfigProtocol"]:
        env = os.getenv("ENV", "production")
        return DevConfig if env == "development" else ProdConfig
    
class ConfigProtocol(Protocol):

    def get_credentials() -> DefaultAzureCredential | str: ...

class BaseConfig(metaclass=MetaConfig): ...

class ProdConfig(ConfigProtocol):
    creds = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

    @staticmethod
    def get_credentials() -> DefaultAzureCredential:
        return ProdConfig.creds
    
class DevConfig(ConfigProtocol):
    @staticmethod
    def get_credentials() -> str:
        return os.getenv("Key", "")

Config: Type[ConfigProtocol] = BaseConfig