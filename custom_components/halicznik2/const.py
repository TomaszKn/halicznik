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

DOMAIN = "d0licznik"

DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 300
DEFAULT_METER_MANUFACTURER = "auto"
DEFAULT_TIMEOUT = 0.1

FRAME_FLAG = b"\x7e"


PROTOKOL_OPTIONS = ["auto", "EC1", "PAF"]

SIGNAL_UPDATE_TELEGRAM = "telegram_update"
SIGNAL_NEW_TELEGRAM_SENSOR = "telegram_new_sensor"

SOH = 0x01  # start of header
STX = 0x02  # start of text
ETX = 0x03  # end of text
ACK = 0x06  # acknowledge
CR = 0x0D  # carriage return
LF = 0x0A  # linefeed
BCC = 0x00  # Block check Character will contain the checksum immediately following the data packet

Baudrates_Protocol_Mode_A = 300
Baudrates_Protocol_Mode_B = {'A': 600, 'B': 1200, 'C': 2400, 'D': 4800, 'E': 9600, 'F': 19200,
                             'G': "reserved", 'H': "reserved", 'I': "reserved"}
Baudrates_Protocol_Mode_C = {'0': 300, '1': 600, '2': 1200, '3': 2400, '4': 4800, '5': 9600, '6': 19200,
                             '7': "reserved", '8': "reserved", '9': "reserved"}

# always '3' but it is always initiated by the metering device so it can't be encountered here
Baudrates_Protocol_Mode_D = {'3': 2400}
Baudrates_Protocol_Mode_E = Baudrates_Protocol_Mode_C