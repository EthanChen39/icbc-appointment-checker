import os
import time
import datetime
import signal
import dotenv
from loguru import logger
from driver_config import DriverConfig
from icbc_client import ICBCClient
from pushover_client import PushOverClient
from appointment_checker import AppointmentChecker


def signal_handler(signum, frame):
    """
    Signal handler to gracefully stop the program.
    """
    logger.info("Signal received, shutting down...")
    global appointment_checker
    appointment_checker.stop_scheduler()
    exit(0)


if __name__ == "__main__":
    dotenv.load_dotenv()
    logger.add(
        f"logs/icbc_appointment_checker_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
        rotation="300 MB",
    )

    # Configuration
    my_icbc_config = DriverConfig(
        license_number=os.getenv("LICENSE_NUMBER"),
        last_name=os.getenv("DRIVER_LAST_NAME"),
        exam_type=os.getenv("EXAM_TYPE"),
        login_keyword=os.getenv("LOGIN_KEYWORD"),
        icbc_office_id=9,  # point grey
    )

    icbc_client = ICBCClient(driver_config=my_icbc_config)
    pushover_client = PushOverClient()

    # Initialize and start appointment checker
    appointment_checker = AppointmentChecker(
        icbc_client, pushover_client, interval=180  # check every 3 minutes
    )

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    appointment_checker.start_scheduler(target_days=30)
    logger.info("Press Ctrl+C to stop the scheduler.")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
