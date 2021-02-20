"""
Decode for HAN Kamstrup.

This module will decode the incoming message from Mbus serial.
"""
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


def parse_data(stored, data, reqs = None):
    """Parse the incoming data to dict."""
    sensor_data = {}
    han_data = {}
    pkt = data
    # current date and time
    now = datetime.now()

    #reqs = reqs.decode()
    reqs = str(reqs)

    if reqs:
        try:
            #manid = str(reqs[1:4], 'asci')
            manid = reqs[1:4]
        except:
            manid = " "

        try:
            #modelid = str(reqs[6:8], 'asci')
            modelid = reqs[6:9]
        except:
            modelid = " "

    if (pkt != ""):
        try:
            pkt = pkt.decode()
            x = pkt.split('(')
        except:
            pass
        if (len (x) > 0):

            address = x[0]
            _LOGGER.debug("adress data: {}".format(address))
            x = x[1][:-2].split(' ')  # the standard seems to have a '*' instead of ' ' here
            value = x[0]
            if value.endswith(')'):
                value = value[:-1]
            try:
                value = float(value)
            except ValueError:
                pass
            _LOGGER.debug("value = data: {}".format(value))
            try:
                unit = '[' + x[1] + ']'
            except:
                unit = ""

            try:
                secvalue = x[1]
            except:
                secvalue = ""

            sensor_data[address] = {
                "state": value,
                "attributes": {
                    "timestamp": now,
                    "meter_timestamp": "2021-02-13",
                    "meter_manufacturer": manid,
                    "meter_type": "Energy",
                    "meter_serial": modelid,
                    "obis_code": address,
                    "obis_telegram": pkt,
                    "reqs": reqs,
                    "secvalue": secvalue,
                    "unit_of_measurement": unit,
                    "icon": "mdi:gauge",
                },
            }

    """
    han_data["obis_r_e_n"] = field_type(".", fields=pkt[240:246])
    han_data["reactive_energy_n"] = byte_decode(fields=pkt[247:251]) / 100
    sensor_data["ams_reactive_energy_export"] = {
        "state": han_data["reactive_energy_n"],
        "attributes": {
            "timestamp": han_data["date_time"],
            "meter_timestamp": han_data["meter_date_time"],
            "meter_manufacturer": han_data["obis_list_version"].title(),
            "meter_type": han_data["meter_type_str"],
            "meter_serial": han_data["meter_serial"],
            "obis_code": han_data["obis_r_e_n"],
            "unit_of_measurement": "kVArh",
            "icon": "mdi:gauge",
        },
    }
    """

    stored.update(sensor_data)
    return stored, han_data
