"""AMS hub platform."""
import logging
import threading
from copy import deepcopy
import time

import homeassistant.helpers.config_validation as cv
import serial
import voluptuous as vol
from serial import SerialException
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import (
    LICZNIK_DEVICES,
    CONF_SERIAL_PORT,
    CONF_METER_MANUFACTURER,
    CONF_BAUDRATE,
    DEFAULT_BAUDRATE,
    DEFAULT_METER_MANUFACTURER,
    DEFAULT_SERIAL_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    FRAME_FLAG,
    SIGNAL_NEW_TELEGRAM_SENSOR,
    SIGNAL_UPDATE_TELEGRAM,
    # Baudrates_Protocol_Mode_A,
    # Baudrates_Protocol_Mode_B,
)
from .parsers import EC3 as EC3

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): cv.string,
                vol.Required(
                    CONF_METER_MANUFACTURER, default=DEFAULT_METER_MANUFACTURER
                ): cv.string,
                vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def _ustawienia(hass, config):
    """Setup helper for the component."""
    if DOMAIN not in hass.data:
        hub = LiHub(hass, config)
        hass.data[DOMAIN] = hub


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """AMS hub YAML setup."""
    # _ustawienia(hass, config[DOMAIN])
    # if config.get(DOMAIN) is None:
    #    _LOGGER.info("No YAML config available, using config_entries")
    #    return True
    _ustawienia(hass, config[DOMAIN])
    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AMS as config entry."""
    _ustawienia(hass, entry.data)
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True


async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    await hass.async_add_executor_job(hass.data[DOMAIN].stop_serial_read)
    return True


class LiHub:
    """AmsHub wrapper for all sensors."""

    def __init__(self, hass, entry):
        """Initialize the AMS hub."""
        self._hass = hass
        port = entry[CONF_SERIAL_PORT]
        _LOGGER.debug("Connecting to HAN using port %s", port)
        parity = serial.PARITY_EVEN
        self.meter_manufacturer = entry.get(CONF_METER_MANUFACTURER)
        self.sensor_data = {}
        self._attrs = {}
        self._running = True
        self._ser = serial.Serial(
            port=port,
            baudrate=300,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.SEVENBITS,
            timeout=DEFAULT_TIMEOUT,
        )
        # self.starthar = entry[SOH]
        self.connection = threading.Thread(target=self.connect, daemon=True)
        self.connection.start()
        _LOGGER.debug("Finish init of LICZNIK")

    def stop_serial_read(self):
        """Close resources."""
        _LOGGER.debug("stop_serial_read")
        self._running = False
        self.connection.join()
        self._ser.close()

    def read_bytes(self):
        """Read the raw data from serial port."""
        byte_counter = 0
        bytelist = []
        while self._running:

            buf = self._ser.read()
            if buf:
                bytelist.extend(buf)
                if buf == FRAME_FLAG and byte_counter > 1:
                    return bytelist
                byte_counter = byte_counter + 1
            else:
                continue

    @property
    def meter_serial(self):
        return self._attrs["meter_serial"]

    @property
    def meter_type(self):
        return self._attrs["meter_type"]

    def connect(self):
        """Read the data from the port."""

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

        InitialBaudrate = 300
        wait_before_acknowledge = 0.4  # wait for 400 ms before sending the request to change baudrate
        wait_after_acknowledge = 0.4  # wait for 400 ms after sending acknowledge

        parser = None

        if self.meter_manufacturer == "auto":
            """
            while parser is None:
                _LOGGER.info("Autodetecting meter manufacturer")
                pkg = self.read_bytes()
                self.meter_manufacturer = self._find_parser(pkg)
                parser = self.meter_manufacturer
            """
            pass

        if self.meter_manufacturer == "ec3":
            parser = EC3

        while self._running:
            #try:
            """
            data = self.read_bytes()
            if parser.test_valid_data(data):
                _LOGGER.debug("data read from port=%s", data)
                self.sensor_data, _ = parser.parse_data(self.sensor_data, data)
                self._check_for_new_sensors_and_update(self.sensor_data)
            else:
                _LOGGER.debug("failed package: %s", data)
            """
            starttime = time.time()
            runtime = starttime
            _LOGGER.info("Start While")
            # _LOGGER.debug("Time to open serial port {}: {}".format(self._ser, self.format_time((5))))
            # runtime = time.time()
            _LOGGER.debug("Time to open serial port {}".format(self._ser))
            self._ser.baudrate = InitialBaudrate
            init_seq = bytes('/?!\r\n', 'ascii')

            try:
                self._ser.write(init_seq)
            except SerialException as exc:
                _LOGGER.exception(
                    "Error while write serial device %s: %s", self._ser, exc
                )
                # await self._handle_error()
                break
            ret = None
            # ret = self.read_data_block_from_serial(self._ser)
            time.sleep(0.1)
            ret = self.read_data_block_from_serial(end_byte=10)

            if ret is None:
                _LOGGER.debug("Brak odpowiedzi na first request")
                time.sleep(10)
                continue

            Identification_Message = ret
            _LOGGER.debug("Identification Message is {}".format(Identification_Message))

            # need at least 7 bytes:
            # 1 byte "/"
            # 3 bytes short Identification
            # 1 byte speed indication
            # 2 bytes CR LF
            if (len(Identification_Message) < 7):
                _LOGGER.warning(
                    "malformed identification message: '{}', abort query".format(Identification_Message))
                time.sleep(10)
                # return
                continue

            if (Identification_Message[0] != 47):
                _LOGGER.warning("identification message '{}' does not start with '/',"
                                "abort query, start with: {} , SOH = {}".format(Identification_Message,
                                                                                Identification_Message[0],
                                                                                str(SOH)))
                # return
                time.sleep(10)
                continue

            manid = str(Identification_Message[1:4], 'utf-8')

            Baudrate_identification = chr(Identification_Message[4])
            #Baudrate_identification = '0'

            if Baudrate_identification in Baudrates_Protocol_Mode_B:
                NewBaudrate = Baudrates_Protocol_Mode_B[Baudrate_identification]
                Protocol_Mode = 'B'
            elif Baudrate_identification in Baudrates_Protocol_Mode_C:
                NewBaudrate = Baudrates_Protocol_Mode_C[Baudrate_identification]
                Protocol_Mode = 'C'  # could also be 'E' but it doesn't make any difference here
            else:
                NewBaudrate = Baudrates_Protocol_Mode_A
                Protocol_Mode = 'A'

            # for protocol C or E we now send an acknowledge and include the new baudrate parameter
            # maybe todo
            # we could implement here a baudrate that is fixed to somewhat lower speed if we need to
            # read out a smartmeter with broken communication
            # Action = b'0'  # Data readout, possible are also b'1' for programming mode or some manufacturer specific

            # Acknowledge = b'\x060' + Baudrate_identification.encode() + Action + b'\r\n'

            try:
                acko = '\x060' + Baudrate_identification + '0\r\n'
                Acknowledge = bytearray(acko, 'ascii')
            except Exception as e:
                _LOGGER.error("Konwersja Acknowledge: {0}".format(e))
                continue

            if Protocol_Mode == 'C':
                # the speed change in communication is initiated from the reading device
                time.sleep(0.4)
                _LOGGER.debug("Using protocol mode C, send acknowledge {} "
                              "and tell smartmeter to switch to {} Baud".format(Acknowledge, NewBaudrate))
                try:
                    self._ser.write(Acknowledge)
                except Exception as e:
                    _LOGGER.warning("Warning {0}".format(e))
                    # return
                    continue
                time.sleep(0.4)
                # dlms_serial.flush()
                # dlms_serial.reset_input_buffer()
                if (NewBaudrate != InitialBaudrate):
                    # change request to set higher baudrate
                    self._ser.baudrate = NewBaudrate
                    _LOGGER.debug("Nowa predkosc")
            # response = self.read_data_block_from_serial(self._ser)
            _LOGGER.info("READ Full DATA")

            licznik = 0
            while True:
                response = None
                response = self.read_data_block_from_serial()
                if response is None:
                    _LOGGER.debug("No data received upon first request")
                    time.sleep(10)
                    licznik = licznik + 1
                    if licznik > 3:
                        break

                    continue
                    # break

                # if licznik > 3:
                #    break

                if len(response) and licznik > 3:
                    break

                _LOGGER.debug("Time for reading OBIS data: ")
                runtime = time.time()

                _LOGGER.debug("OBIS data: Telegram{}".format(response))
                self.sensor_data, _ = parser.parse_data(self.sensor_data, response)
                self._check_for_new_sensors_and_update(self.sensor_data)

            #break


            #except serial.serialutil.SerialException:
            #    pass

        _LOGGER.debug("Koniec pętli pętla")

    def _find_parser(self, pkg):
        """Helper to detect meter manufacturer."""
        """
        if _test_meter(pkg, AIDON_METER_SEQ):
            _LOGGER.info("Detected Adion meter")
            return "aidon"
        elif _test_meter(pkg, KAIFA_METER_SEQ):
            _LOGGER.info("Detected Kaifa meter")
            return "kaifa"
        elif _test_meter(pkg, KAMSTRUP_METER_SEQ):
            _LOGGER.info("Detected Kamstrup meter")
            return "kamstrup"
        _LOGGER.warning("No parser detected")
        """
        pass

    @property
    def data(self):
        """Return sensor data."""
        return self.sensor_data

    def missing_attrs(self, data=None):
        """Check if we have any missing attrs that we need and set them."""

        if data is None:
            data = self.data

        # return False

        attrs_to_check = ["meter_serial", "meter_manufacturer", "meter_type"]
        miss_attrs = [i for i in attrs_to_check if i not in self._attrs]
        if miss_attrs:
            cp_sensors_data = deepcopy(data)
            for check in miss_attrs:
                for value in cp_sensors_data.values():
                    v = value.get("attributes", {}).get(check)
                    if v:
                        self._attrs[check] = v
                        break
            del cp_sensors_data
            if len([i for i in attrs_to_check if i not in self._attrs]):
                return True
            else:
                return False
        else:
            return False

    def _check_for_new_sensors_and_update(self, sensor_data):
        """Compare sensor list and update."""
        new_devices = []
        sensors_in_data = set(sensor_data.keys())
        new_devices = sensors_in_data.difference(LICZNIK_DEVICES)

        if len(new_devices):
            # Check that we have all the info we need before the sensors are
            # created, the most importent one is the meter_serial as this is
            # use to create the unique_id
            if self.missing_attrs(sensor_data) is True:
                _LOGGER.debug(
                    "Missing some attributes waiting for new read from the serial"
                )
            else:
                _LOGGER.debug("Got %s new devices from the serial", len(new_devices))
                _LOGGER.debug("DUMP %s", sensor_data)
                async_dispatcher_send(self._hass, SIGNAL_NEW_TELEGRAM_SENSOR)
        else:
            _LOGGER.debug("sensors are the same, updating states")
            async_dispatcher_send(self._hass, SIGNAL_UPDATE_TELEGRAM)

    def read_data_block_from_serial(self, end_byte=0x0a):
        """
        This function reads some bytes from serial interface
        it returns an array of bytes if a timeout occurs or a given end byte is encountered
        and otherwise None if an error occurred
        :param the_serial: interface to read from
        :param end_byte: the indicator for end of data by source endpoint
        :returns the read data or None
        """
        response = bytes()
        krok = 0
        try:
            while True:
                ch = self._ser.read()
                # _LOGGER.debug("read_data_block_from_serial Read {}".format(ch))
                if len(ch) == 0:
                    if krok < 50:
                        time.sleep(0.02)
                        continue
                    else:
                        _LOGGER.debug("read_data_block_from_serial Len = 0 break")
                        return None
                        break

                #if ch < 1:
                #    _LOGGER.debug("read_data_block_from_serial Len = 0 break")
                #    #return None
                #    break

                response += ch
                if ch == end_byte:
                    _LOGGER.debug("read_data_block_from_serial ch == end_byte break")
                    break
                if (response[-1] == end_byte):
                    _LOGGER.debug("read_data_block_from_serial response[-1] == end_byte break")
                    break

                time.sleep(0.01)
        except Exception as e:
            _LOGGER.debug("read_data_block_from_serial Warning {0}".format(e))
            return None

        return response

    def format_time(self, timedelta):
        """
        returns a pretty formatted string according to the size of the timedelta
        :param timediff: time delta given in seconds
        :return: returns a string
        """
        if timedelta > 1000.0:
            return "{:.2f} s".format(timedelta)
        elif timedelta > 1.0:
            return "{:.2f} s".format(timedelta)
        elif timedelta > 0.001:
            return "{:.2f} ms".format(timedelta * 1000.0)
        elif timedelta > 0.000001:
            return "{:.2f} µs".format(timedelta * 1000000.0)
        elif timedelta > 0.000000001:
            return "{:.2f} ns".format(timedelta * 1000000000.0)
