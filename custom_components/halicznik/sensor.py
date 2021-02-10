"""Support for reading data from a serial port."""
import asyncio
import json
import logging

from serial import SerialException
import serial_asyncio
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_XONXOFF = "xonxoff"
CONF_RTSCTS = "rtscts"
CONF_DSRDTR = "dsrdtr"

DEFAULT_NAME = "Interfejs licznika"
DEFAULT_BAUDRATE = 300
DEFAULT_BYTESIZE = serial_asyncio.serial.SEVENBITS
DEFAULT_PARITY = serial_asyncio.serial.PARITY_EVEN
DEFAULT_STOPBITS = serial_asyncio.serial.STOPBITS_ONE
DEFAULT_XONXOFF = False
DEFAULT_RTSCTS = False
DEFAULT_DSRDTR = False

SOH = 0x01  # start of header
STX = 0x02  # start of text
ETX = 0x03  # end of text
ACK = 0x06  # acknowledge
CR = 0x0D  # carriage return
LF = 0x0A  # linefeed
BCC = 0x00  # Block check Character will contain the checksum immediately following the data packet
#StartChar = b'/'[0]
StartChar = STX
InitialBaudrate = 300


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): vol.In(
            [
                serial_asyncio.serial.FIVEBITS,
                serial_asyncio.serial.SIXBITS,
                serial_asyncio.serial.SEVENBITS,
                serial_asyncio.serial.EIGHTBITS,
            ]
        ),
        vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): vol.In(
            [
                serial_asyncio.serial.PARITY_NONE,
                serial_asyncio.serial.PARITY_EVEN,
                serial_asyncio.serial.PARITY_ODD,
                serial_asyncio.serial.PARITY_MARK,
                serial_asyncio.serial.PARITY_SPACE,
            ]
        ),
        vol.Optional(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.In(
            [
                serial_asyncio.serial.STOPBITS_ONE,
                serial_asyncio.serial.STOPBITS_ONE_POINT_FIVE,
                serial_asyncio.serial.STOPBITS_TWO,
            ]
        ),
        vol.Optional(CONF_XONXOFF, default=DEFAULT_XONXOFF): cv.boolean,
        vol.Optional(CONF_RTSCTS, default=DEFAULT_RTSCTS): cv.boolean,
        vol.Optional(CONF_DSRDTR, default=DEFAULT_DSRDTR): cv.boolean,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Serial sensor platform."""
    name = config.get(CONF_NAME)
    port = config.get(CONF_SERIAL_PORT)
    baudrate = config.get(CONF_BAUDRATE)
    bytesize = config.get(CONF_BYTESIZE)
    parity = config.get(CONF_PARITY)
    stopbits = config.get(CONF_STOPBITS)
    xonxoff = config.get(CONF_XONXOFF)
    rtscts = config.get(CONF_RTSCTS)
    dsrdtr = config.get(CONF_DSRDTR)

    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    sensor = SerialSensor(
        name,
        port,
        baudrate,
        bytesize,
        parity,
        stopbits,
        xonxoff,
        rtscts,
        dsrdtr,
        value_template,
    )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, sensor.stop_serial_read)
    async_add_entities([sensor], True)

async def read_data_block_from_serial(the_serial, end_byte=0x0a):
    """
    This function reads some bytes from serial interface
    it returns an array of bytes if a timeout occurs or a given end byte is encountered
    and otherwise None if an error occurred
    :param the_serial: interface to read from
    :param end_byte: the indicator for end of data by source endpoint
    :returns the read data or None
    """
    response = bytes()
    ch=''
    try:
        #_LOGGER.info("start read ")
        while not the_serial.at_eof() :
            #ch = await the_serial.read(1)
            #ch = the_serial.read()
            #response = the_serial.readuntil(end_byte)
            response = await the_serial.readline()
            # logger.debug("Read {}".format(ch))
            #if len(ch) == 0:
            #if not ch:
            #    break
            #response += ch
            #if ch == end_byte:
            #    break
            #if (response[-1] == end_byte):
            #    break
            await asyncio.sleep(0.01)
    except Exception as e:
        _LOGGER.debug("Warning read_data_block_from_serial: {0}".format(e))
        return None
    if response[0] == 0:
        return None
    return response

class SerialSensor(Entity):
    """Representation of a Serial sensor."""

    def __init__(
        self,
        name,
        port,
        baudrate,
        bytesize,
        parity,
        stopbits,
        xonxoff,
        rtscts,
        dsrdtr,
        value_template,
    ):
        """Initialize the Serial sensor."""
        self._name = name
        self._state = None
        self._port = port
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._xonxoff = xonxoff
        self._rtscts = rtscts
        self._dsrdtr = dsrdtr
        self._serial_loop_task = None
        self._template = value_template
        self._attributes = None

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        self._serial_loop_task = self.hass.loop.create_task(
            self.serial_read(
                self._port,
                self._baudrate,
                self._bytesize,
                self._parity,
                self._stopbits,
                self._xonxoff,
                self._rtscts,
                self._dsrdtr,
            )
        )



    async def serial_read(
        self,
        device,
        baudrate,
        bytesize,
        parity,
        stopbits,
        xonxoff,
        rtscts,
        dsrdtr,
        **kwargs,
    ):
        """Read the data from the port."""
        _LOGGER.info("init")
        # open the serial communication
        # about timeout: time tr between sending a request and an answer needs to be
        # 200ms < tr < 1500ms for protocol mode A or B
        # inter character time must be smaller than 1500 ms
        # The time between the reception of a message and the transmission of an answer is:
        # (20 ms) 200 ms = tr = 1 500 ms (see item 12) of 6.3.14).
        # If a response has not been received, the waiting time of the transmitting equipment after
        # transmission of the identification message, before it continues with the transmission, is:
        # 1 500 ms < tt = 2 200 ms
        # The time between two characters in a character sequence is:
        # ta < 1 500 ms
        wait_before_acknowledge = 0.4  # wait for 400 ms before sending the request to change baudrate
        wait_after_acknowledge = 0.4  # wait for 400 ms after sending acknowledge

        logged_error = False
        while True:
            try:
                reader, writer = await serial_asyncio.open_serial_connection(
                    url=device,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    xonxoff=xonxoff,
                    rtscts=rtscts,
                    dsrdtr=dsrdtr,
                    **kwargs,
                )

            except SerialException as exc:
                if not logged_error:
                    _LOGGER.exception(
                        "Unable to connect to the serial device %s: %s. Will retry",
                        device,
                        exc,
                    )
                    logged_error = True
                await self._handle_error()
            else:
                _LOGGER.info("Serial device %s connected", device)
                while True:

                    #Request_message = '/?!\r\n'  # IEC 62056-21:2002(E) 6.3.1
                    init_seq = bytes('/?!\r\n', 'ascii')
                    #await writer.write(init_seq)
                    try:
                        writer.write(init_seq)
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while write serial device %s: %s", device, exc
                        )
                        await self._handle_error()
                        break
                    _LOGGER.info("SEND init_seq ")
                    await asyncio.sleep(0.5)
                    #response = bytes()
                    #Identification_Message = bytes()
                    #response = "k"
                    Identification_Message = ""
                    try:
                        line = await reader.readline()
                        #response = await reader.readline()
                        response = line
                        #response = await read_data_block_from_serial(reader)

                        if response is None:
                            _LOGGER.debug("No response received upon first request")
                            continue

                        encoding = 'ascii'
                        Identification_Message = response.decode(encoding)
                        #Identification_Message = response
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while reading serial device %s: %s", device, exc
                        )
                        await self._handle_error()
                        break
                    else:
                        #_LOGGER.debug("response is {}".format(response))
                        _LOGGER.debug("Identification Message is {}".format(Identification_Message))

                        # need at least 7 bytes:
                        # 1 byte "/"
                        # 3 bytes short Identification
                        # 1 byte speed indication
                        # 2 bytes CR LF
                        if (len(Identification_Message) < 7):
                            _LOGGER.warning(
                                "malformed identification message: '{}', abort query".format(Identification_Message))
                            Identification_Message = ''
                            response = ''

                            await asyncio.sleep(10)
                            reader.flush()
                            continue

                        #if (Identification_Message[0] != StartChar):
                        if (Identification_Message[0] != '/'):
                            _LOGGER.warning("identification message '{}' does not start with '/',"
                                           "abort query".format(Identification_Message))
                            Identification_Message = ''
                            response = ''

                            await asyncio.sleep(10)
                            reader.flush()
                            continue

                        #manid = str(Identification_Message[1:4], 'utf-8')
                        #manname = manufacturer_ids.get(manid, 'unknown')
                        #logger.debug(
                        #    "The manufacturer for {} is {} (out of {} given manufacturers)".format(manid, manname, len(
                        #        manufacturer_ids)))

                        """
                            Different smartmeters allow for different protocol modes. 
                            The protocol mode decides whether the communication is fixed to a certain baudrate or might be speed up.
                            Some meters do initiate a protocol by themselves with a fixed speed of 2400 baud e.g. Mode D
                            However some meters specify a speed of 9600 Baud although they use protocol mode D (readonly)
                            """
                        Protocol_Mode = 'C'

                        """
                        The communication of the plugin always stays at the same speed, 
                        Protocol indicator can be anything except for A-I, 0-9, /, ?
                        """
                        Baudrates_Protocol_Mode_A = 300
                        Baudrates_Protocol_Mode_B = {'A': 600, 'B': 1200, 'C': 2400, 'D': 4800, 'E': 9600, 'F': 19200,
                                                     'G': "reserved", 'H': "reserved", 'I': "reserved"}
                        Baudrates_Protocol_Mode_C = {'0': 300, '1': 600, '2': 1200, '3': 2400, '4': 4800, '5': 9600,
                                                     '6': 19200,
                                                     '7': "reserved", '8': "reserved", '9': "reserved"}

                        # always '3' but it is always initiated by the metering device so it can't be encountered here
                        Baudrates_Protocol_Mode_D = {'3': 2400}
                        Baudrates_Protocol_Mode_E = Baudrates_Protocol_Mode_C
                        _LOGGER.debug("Calculate baud")
                        try:
                            _LOGGER.debug("Baudrate_identification mess: {0}".format(chr(Identification_Message[4])))
                            Baudrate_identification = chr(Identification_Message[4])
                        except Exception as e:
                            _LOGGER.error("Baudrate_identification: {0}".format(e))

                        _LOGGER.debug("Speed code {}".format(Baudrate_identification))
                        if Baudrate_identification in Baudrates_Protocol_Mode_B:
                            NewBaudrate = Baudrates_Protocol_Mode_B[Baudrate_identification]
                            Protocol_Mode = 'B'
                        elif Baudrate_identification in Baudrates_Protocol_Mode_C:
                            NewBaudrate = Baudrates_Protocol_Mode_C[Baudrate_identification]
                            Protocol_Mode = 'C'  # could also be 'E' but it doesn't make any difference here
                        else:
                            NewBaudrate = Baudrates_Protocol_Mode_A
                            Protocol_Mode = 'A'

                        _LOGGER.debug("Baudrate id is '{}' thus Protocol Mode is {} and "
                                     "max Baudrate available is {} Bd".format(Baudrate_identification, Protocol_Mode,
                                                                              NewBaudrate))

                        if chr(Identification_Message[5]) == '\\':
                            if chr(Identification_Message[6]) == '2':
                                _LOGGER.debug("HDLC protocol could be used if it was implemented")
                            else:
                                _LOGGER.debug("Another protocol could probably be used if it was implemented")
                        _LOGGER.debug("Speed code {}".format(Baudrate_identification))

                        # for protocol C or E we now send an acknowledge and include the new baudrate parameter
                        # maybe todo
                        # we could implement here a baudrate that is fixed to somewhat lower speed if we need to
                        # read out a smartmeter with broken communication
                        Action = b'0'  # Data readout, possible are also b'1' for programming mode or some manufacturer specific

                        Acknowledge = b'\x060' + Baudrate_identification.encode() + Action + b'\r\n'

                        if Protocol_Mode == 'C':
                            # the speed change in communication is initiated from the reading device
                            await asyncio.sleep(wait_before_acknowledge)
                            _LOGGER.debug("Using protocol mode C, send acknowledge {} "
                                         "and tell smartmeter to switch to {} Baud".format(Acknowledge, NewBaudrate))
                            try:
                                writer.write(Acknowledge)
                            except Exception as e:
                                _LOGGER.warning("Write Warning {0}".format(e))
                                return
                            await asyncio.sleep(wait_after_acknowledge)
                            # dlms_serial.flush()
                            # dlms_serial.reset_input_buffer()
                            if (NewBaudrate != InitialBaudrate):
                                # change request to set higher baudrate
                                try:
                                    writer.baudrate = NewBaudrate
                                except Exception as e:
                                    _LOGGER.warning("New baudrate Write Warning {0}".format(e))
                                return

                        while True:
                            telegram = await reader.readline()

                            if telegram is None:
                                _LOGGER.debug("No telegram received upon first request")
                                continue

                            encoding = 'ascii'
                            Telegram_Message = telegram.decode(encoding)
                            _LOGGER.warning("New Telegram_Message {0}".format(Telegram_Message))


                        # line = Identification_Message.decode("ascii").strip()
                        line = Identification_Message.strip()

                        try:
                            data = json.loads(line)
                        except ValueError:
                            pass
                        else:
                            if isinstance(data, dict):
                                self._attributes = data

                        if self._template is not None:
                            line = self._template.async_render_with_possible_json_value(
                                line
                            )

                        _LOGGER.debug("Received: %s", line)
                        self._state = line
                        self.async_write_ha_state()
                        await asyncio.sleep(5)


    async def _handle_error(self):
        """Handle error for serial connection."""
        self._state = None
        self._attributes = None
        self.async_write_ha_state()
        await asyncio.sleep(5)

    @callback
    def stop_serial_read(self, event):
        """Close resources."""
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the attributes of the entity (if any JSON present)."""
        return self._attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
