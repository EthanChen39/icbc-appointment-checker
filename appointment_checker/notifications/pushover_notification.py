from pydantic import BaseModel
import requests
from loguru import logger
from .base_notification import BaseNotification
from typing import Dict


class PushoverCredentialsModel(BaseModel):
    api_token: str
    user_key: str
    device: str = "iphone"


class PushoverNotification(BaseNotification):
    PUSH_MESSAGE_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, pushover_config: PushoverCredentialsModel):
        self.api_token = pushover_config.api_token
        self.user_key = pushover_config.user_key
        self.device = pushover_config.device
        self.verify_credentials()
        logger.info(f"{self.__class__.__name__} initialized")

    def verify_credentials(self):
        if not self.api_token or not self.user_key:
            logger.error(
                "API Token or User Key not found. Please ensure they are provided in the configuration."
            )
            raise ValueError("API Token or User Key not found")

    def send(self, message: str, title) -> None:
        message_payload = {
            "token": self.api_token,
            "user": self.user_key,
            "title": title,
            "message": message,
            "priority": 1,
            "device": self.device,
        }

        try:
            response = requests.post(
                url=self.PUSH_MESSAGE_API_URL, data=message_payload
            )
            response.raise_for_status()
            logger.info("Push notification sent successfully.")
        except requests.RequestException as e:
            logger.error(f"Failed to send push notification: {e}")
            raise
