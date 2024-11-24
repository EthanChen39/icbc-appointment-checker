import os
import requests
from loguru import logger


class PushOverClient:
    PUSH_MESSAGE_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self):
        self.__api_token = os.getenv("PUSHOVER_API_TOKEN")
        self.__user_key = os.getenv("PUSHOVER_USER_KEY")
        self.__verify_credentials()
        logger.info(f"{__class__.__name__} initialized")

    def __verify_credentials(self):
        if not self.__api_token or not self.__user_key:
            logger.error(
                "API Token or User Key not found. Please make sure they are set in the .env file."
            )
            raise ValueError("API Token or User Key not found")

    @logger.catch
    def send_message(self, message: str, title: str) -> None:
        message_payload = {
            "token": self.__api_token,
            "user": self.__user_key,
            "title": title,
            "message": message,
            "priority": 1,
            "device": "iphone",
        }

        response = requests.post(url=self.PUSH_MESSAGE_API_URL, data=message_payload)
        response.raise_for_status()

        if response.status_code == 200:
            logger.info("Push notification sent successfully.")
        else:
            logger.error(
                f"Failed to send push notification. Status code: {response.status_code}"
            )
