""" Constants for hass-AMS package"""

import serial

TELEGRAM_NEW_SENSORS = "ams_new_sensors"
TELEGRAM_SENSORS = "ams_sensors"
# Devices that we have read from the serial connection.
LICZNIK_DEVICES = set()
LICZNIK_SENSOR_CREATED_BUT_NOT_READ = set()

CONF_BAUDRATE = "baudrate"
CONF_METER_MANUFACTURER = "meter_manufacturer"
CONF_SERIAL_PORT = "serial_port"

DOMAIN = "halicznik2"

DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 300
DEFAULT_METER_MANUFACTURER = "auto"
DEFAULT_TIMEOUT = 0.1

FRAME_FLAG = b"\x7e"


PROTOKOL_OPTIONS = ["auto", "EC1", "PAF"]

SIGNAL_UPDATE_TELEGRAM = "telegram_update"
SIGNAL_NEW_TELEGRAM_SENSOR = "telegram_new_sensor"

