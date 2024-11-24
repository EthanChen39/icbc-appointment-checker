import requests
import datetime
from driver_config import DriverConfig
from typing import Dict, List
from pydantic import BaseModel, ValidationError
from loguru import logger


class AppointmentModel(BaseModel):
    appointmentDt: Dict
    dlExam: Dict
    endTm: str
    lemgMsgId: int
    posId: int
    resourceId: int
    signature: str
    startTm: str


class ICBCClient:
    TOKEN_TIMEOUT = datetime.timedelta(minutes=15)  # Token validity duration

    @logger.catch
    def __init__(self, driver_config: DriverConfig) -> None:
        self.__headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": "macOS",
            "Content-Type": "application/json",
        }
        self.__driver_config: DriverConfig = driver_config
        self.__auth_token: str = ""
        self.__token_acquired_time: datetime.datetime | None = None
        self.__refresh_token()

    @logger.catch
    def __refresh_token(self) -> None:
        """
        Logs in and refreshes the authorization token.
        """
        self.__icbc_login_url: str = (
            "https://onlinebusiness.icbc.com/deas-api/v1/webLogin/webLogin"
        )

        # Construct login header
        login_header = self.__headers.copy()
        login_header["Referer"] = (
            "https://onlinebusiness.icbc.com/webdeas-ui/login;type=driver"
        )
        login_header["Cache-Control"] = "no-cache, no-store"

        # Construct login body
        login_body = {
            "drvrLastName": self.__driver_config.last_name,
            "keyword": self.__driver_config.login_keyword,
            "licenceNumber": self.__driver_config.license_number,
        }

        logger.info("Logging into ICBC")
        response = requests.put(
            url=self.__icbc_login_url, json=login_body, headers=login_header
        )

        # Check if login was successful
        if response.status_code == 200:
            authorization_token: str | None = response.headers.get("Authorization")
            assert authorization_token is not None
            logger.success(
                "ICBC login was successful, and Authorization Token was received"
            )
            self.__auth_token = authorization_token
            self.__token_acquired_time = datetime.datetime.now()
        else:
            logger.error(f"Failed to login. Status code: {response.status_code}")
            logger.error(response.json())
            raise RuntimeError("Failed to login ICBC. Check your credentials.")

    @logger.catch
    def __ensure_token_valid(self) -> None:
        """
        Ensures that the auth token is still valid. Refreshes if expired.
        """
        if (
            self.__token_acquired_time is None
            or datetime.datetime.now() - self.__token_acquired_time > self.TOKEN_TIMEOUT
        ):
            logger.info("Token expired or not set. Refreshing token.")
            self.__refresh_token()

    @logger.catch
    def get_available_road_test_appointments(self) -> List[AppointmentModel]:
        self.__ensure_token_valid()  # Ensure the token is valid before the request
        icbc_road_test_appointment_url: str = (
            "https://onlinebusiness.icbc.com/deas-api/v1/web/getAvailableAppointments"
        )
        # Get tomorrow's date
        tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_str = tomorrow_date.strftime("%Y-%m-%d")

        # Construct appointment headers
        appointment_headers = self.__headers.copy()
        appointment_headers["Authorization"] = self.__auth_token
        appointment_headers["Referer"] = (
            "https://onlinebusiness.icbc.com/webdeas-ui/booking"
        )

        body_payload = {
            "aPosID": (
                self.__driver_config.icbc_office_id
                if self.__driver_config.icbc_office_id is not None
                else 9
            ),
            "examType": self.__driver_config.exam_type,
            "examDate": tomorrow_str,
            "ignoreReserveTime": False,
            "prfDaysOfWeek": "[0,1,2,3,4,5,6]",
            "prfPartsOfDay": "[0,1]",
            "lastName": self.__driver_config.last_name,
            "licenseNumber": self.__driver_config.license_number,
        }

        response = requests.post(
            url=icbc_road_test_appointment_url,
            json=body_payload,
            headers=appointment_headers,
        )

        if response.status_code == 200:
            try:
                # Parse the response into a list of AppointmentModel
                appointments = [
                    AppointmentModel(**appointment) for appointment in response.json()
                ]
                logger.info(f"Successfully fetched {len(appointments)} appointments")
                return appointments
            except ValidationError as e:
                logger.error("Error parsing response:", e)
                return []
        else:
            logger.error(
                f"Failed to fetch appointments. Status code: {response.status_code}"
            )
            return []
