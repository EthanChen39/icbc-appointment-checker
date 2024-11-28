from abc import ABC, abstractmethod


class BaseNotification(ABC):
    @abstractmethod
    def send(self, message: str, title: str = "Notification") -> None:
        pass
