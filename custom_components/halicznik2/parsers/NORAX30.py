"""
Decode for HAN Kamstrup.

This module will decode the incoming message from Mbus serial.
"""
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

kody = {'1-0:15.8.0': ['Sum total', 'kWh', 'TAK'],
        '1-0:0.0.0': ['Serial number', '', 'NIE'],
        '1-0:31.7.0': ['Prąd chwilowy, faza L1', '', 'TAK'],
        '1-0:32.7.0': ['Napięcie chwilowe, faza L1', '', 'TAK'],
        '1-0:51.7.0': ['Prąd chwilowy, faza L2', '', 'TAK'],
        '1-0:52.7.0': ['Napięcie chwilowe, faza L2', '', 'TAK'],
        '1-0:71.7.0': ['Prąd chwilowy, faza L3', '', 'TAK'],
        '1-0:72.7.0': ['Napięcie chwilowe, faza L3', '', 'TAK'],
        }


def parse_data(stored, data, reqs = None):
    """Parse the incoming data to dict."""
    sensor_data = {}
    han_data = {}
    pkt = data
    # current date and time
    now = datetime.now()

    #reqs = reqs.decode()

    try:
        reqs = str(reqs)
        manid = reqs[1:4]
    except:
        manid = " "

    try:
        modelid = reqs[7:13]
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
            try:
                wa = x[1][:-1].split('*')  # the standard seems to have a '*' instead of ' ' here
                value = wa[0]
            except:
                value = ""
                pass

            if value.endswith(')'):
                value = value[:-1]

            if address in kody:
                opis = kody.get(address)[0]
                unit = kody.get(address)[1]

                if kody.get(address)[2] == 'TAK':
                    try:
                        value = float(value)
                    except ValueError:
                        pass

            else:
                unit = ""
                opis = ""

            try:
                unit = wa[1]
            except:
                pass

            if unit.endswith(')'):
                unit = unit[:-1]

            _LOGGER.debug("value = data: {}".format(value))

            try:
                secvalue = x[2][:-1]
            except:
                secvalue = ""

            if secvalue.endswith(')'):
                secvalue = secvalue[:-1]

            sensor_data[address] = {
                "state": value,
                "attributes": {
                    "Opis" : opis,
                    "timestamp": now,
                    #"meter_timestamp": "2021-02-13",
                    "meter_manufacturer": manid,
                    "meter_type": "Energy",
                    "meter_serial": modelid,
                    #"obis_code": address,
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
