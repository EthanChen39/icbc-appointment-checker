import datetime
import threading
from typing import List
from loguru import logger
from icbc_client import ICBCClient, AppointmentModel
from pushover_client import PushOverClient


class AppointmentChecker:
    def __init__(
        self,
        icbc_client: ICBCClient,
        pushover_client: PushOverClient,
        interval: int = 300,
    ):
        """
        Initialize the AppointmentChecker with clients and periodic interval.

        :param icbc_client: Instance of ICBCClient
        :param pushover_client: Instance of PushOverClient
        :param interval: Time interval in seconds for periodic checks (default 5 mins)
        """
        self.icbc_client = icbc_client
        self.pushover_client = pushover_client
        self.interval = interval
        self.stop_event = threading.Event()  # Event to signal the thread to stop
        self.scheduler_thread = None

    @staticmethod
    @logger.catch
    def is_appointment_available_within_n_days(
        n_days: int, appointment: AppointmentModel
    ) -> bool:
        """
        Check if the appointment is available within n_days.
        """
        appointment_date = appointment.appointmentDt.get("date")
        appointment_date_obj = datetime.datetime.strptime(appointment_date, "%Y-%m-%d")
        today_date = datetime.date.today()
        n_days_later = today_date + datetime.timedelta(days=n_days)
        return today_date <= appointment_date_obj.date() <= n_days_later

    @logger.catch
    def notify_user(self, appointments: List[AppointmentModel]) -> None:
        """
        Notify the user of the available appointments via Pushover.
        """
        title = "ICBC Road Test Appointments Available"
        message = "The following appointments are available:\n"
        for appointment in appointments:
            appointment_date_dict = appointment.appointmentDt
            appointment_date = appointment_date_dict.get("date")
            appointment_day_of_week = appointment_date_dict.get("dayOfWeek")
            start_time = appointment.startTm
            end_time = appointment.endTm

            message += f"Date: {appointment_date} ({appointment_day_of_week})\n"
            message += f"Time: {start_time} - {end_time}\n\n"

        self.pushover_client.send_message(title=title, message=message)

    def fetch_and_notify(self, target_days: int = 30) -> None:
        """
        Fetch appointments and notify the user if desired appointments are found.
        """
        try:
            logger.info("Fetching available appointments...")
            appointments = self.icbc_client.get_available_road_test_appointments()

            logger.info(f"Fetched {len(appointments)} appointments.")

            # Filter appointments within the target days
            desired_appointments = [
                appt
                for appt in appointments
                if self.is_appointment_available_within_n_days(target_days, appt)
            ]

            if desired_appointments:
                logger.info(f"Found {len(desired_appointments)} desired appointments.")
                self.notify_user(desired_appointments)
            else:
                logger.warning("No desired appointments found.")

        except Exception as e:
            logger.error(f"Error fetching or notifying: {e}")

    def start_scheduler(self, target_days: int = 30) -> None:
        """
        Start the periodic scheduler to fetch and notify.
        """
        logger.info("Starting the appointment checker scheduler...")

        def run_periodically():
            while not self.stop_event.is_set():
                self.fetch_and_notify(target_days)
                # Wait for the interval or stop signal
                if self.stop_event.wait(self.interval):
                    break

        self.scheduler_thread = threading.Thread(target=run_periodically, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self) -> None:
        """
        Stop the periodic scheduler.
        """
        logger.info("Stopping the appointment checker scheduler...")
        self.stop_event.set()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join()
        logger.info("Appointment checker scheduler stopped.")
