from abc import ABC, abstractmethod

class UnsupportedPlatformException(Exception):
    ...

class Plugin(ABC):
    @staticmethod
    @abstractmethod
    def execute(config: dict) -> NotImplementedError:
        raise NotImplementedError
