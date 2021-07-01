#!/usr/bin/env python3
"""Support for Tuya switches."""

import json
import logging
from typing import List, Optional

from tuya_iot import TuyaDevice, TuyaDeviceManager

from homeassistant.components.sensor import DOMAIN as DEVICE_DOMAIN, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .base import TuyaHaDevice
from .const import (
    DOMAIN,
    TUYA_DEVICE_MANAGER,
    TUYA_DISCOVERY_NEW,
    TUYA_HA_DEVICES,
    TUYA_HA_TUYA_MAP,
)

_LOGGER = logging.getLogger(__name__)

TUYA_SUPPORT_TYPE = [
    "wsdcg",  # Temperature and Humidity Sensor
    "mcs",  # Door Window Sensor
    "ywbj",  # Somke Detector
    "rqbj",  # Gas Detector
    "pir",  # PIR Detector
    "sj",  # Water Detector
    "pm2.5",  # PM2.5 Sensor
    "kg",  # Switch
    "cz",  # Socket
    "pc",  # Power Strip
    "wk",  # Thermostat
]

# Smoke Detector
# https://developer.tuya.com/en/docs/iot/s?id=K9gf48r5i2iiy
DPCODE_BATTERY = "va_battery"
DPCODE_BATTERY_PERCENTAGE = "battery_percentage"
DPCODE_BATTERY_CODE = "battery"

DPCODE_TEMPERATURE = "va_temperature"
DPCODE_HUMIDITY = "va_humidity"

DPCODE_PM100_VALUE = "pm100_value"
DPCODE_PM25_VALUE = "pm25_value"
DPCODE_PM10_VALUE = "pm10_value"

DPCODE_TEMP_CURRENT = "temp_current"
DPCODE_HUMIDITY_VALUE = "humidity_value"

DPCODE_CURRENT = "cur_current"
DPCODE_POWER = "cur_power"
DPCODE_VOLTAGE = "cur_voltage"


async def async_setup_entry(
    hass: HomeAssistant, _entry: ConfigEntry, async_add_entities
):
    """Set up tuya sensors dynamically through tuya discovery."""
    _LOGGER.info("sensor init")

    hass.data[DOMAIN][TUYA_HA_TUYA_MAP].update({DEVICE_DOMAIN: TUYA_SUPPORT_TYPE})

    async def async_discover_device(dev_ids):
        """Discover and add a discovered tuya sensor."""
        _LOGGER.info(f"sensor add-> {dev_ids}")
        if not dev_ids:
            return
        entities = await hass.async_add_executor_job(_setup_entities, hass, dev_ids)
        hass.data[DOMAIN][TUYA_HA_DEVICES].extend(entities)
        async_add_entities(entities)

    async_dispatcher_connect(
        hass, TUYA_DISCOVERY_NEW.format(DEVICE_DOMAIN), async_discover_device
    )

    device_manager = hass.data[DOMAIN][TUYA_DEVICE_MANAGER]
    device_ids = []
    for (device_id, device) in device_manager.device_map.items():
        if device.category in TUYA_SUPPORT_TYPE:
            device_ids.append(device_id)
    await async_discover_device(device_ids)


def _setup_entities(hass, device_ids: List):
    """Set up Tuya Switch device."""
    device_manager = hass.data[DOMAIN][TUYA_DEVICE_MANAGER]
    entities = []
    for device_id in device_ids:
        device = device_manager.device_map[device_id]
        if device is None:
            continue

        if DPCODE_BATTERY in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_BATTERY,
                    DPCODE_BATTERY,
                    PERCENTAGE,
                )
            )
        if DPCODE_BATTERY_PERCENTAGE in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_BATTERY,
                    DPCODE_BATTERY_PERCENTAGE,
                    PERCENTAGE,
                )
            )
        if DPCODE_BATTERY_CODE in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_BATTERY,
                    DPCODE_BATTERY_CODE,
                    PERCENTAGE,
                )
            )

        if DPCODE_TEMPERATURE in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_TEMPERATURE,
                    DPCODE_TEMPERATURE,
                    TEMP_CELSIUS,
                )
            )
        if DPCODE_TEMP_CURRENT in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_TEMPERATURE,
                    DPCODE_TEMP_CURRENT,
                    TEMP_CELSIUS,
                )
            )

        if DPCODE_HUMIDITY in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_HUMIDITY,
                    DPCODE_HUMIDITY,
                    PERCENTAGE,
                )
            )
        if DPCODE_HUMIDITY_VALUE in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_HUMIDITY,
                    DPCODE_HUMIDITY_VALUE,
                    PERCENTAGE,
                )
            )

        if DPCODE_PM100_VALUE in device.status:
            entities.append(
                TuyaHaSensor(
                    device, device_manager, "PM10", DPCODE_PM100_VALUE, "ug/m³"
                )
            )
        if DPCODE_PM25_VALUE in device.status:
            entities.append(
                TuyaHaSensor(
                    device, device_manager, "PM2.5", DPCODE_PM25_VALUE, "ug/m³"
                )
            )
        if DPCODE_PM10_VALUE in device.status:
            entities.append(
                TuyaHaSensor(
                    device, device_manager, "PM1.0", DPCODE_PM10_VALUE, "ug/m³"
                )
            )

        if DPCODE_CURRENT in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    "Current",
                    DPCODE_CURRENT,
                    json.loads(device.status_range.get(DPCODE_CURRENT).values).get(
                        "unit", 0
                    ),
                )
            )
        if DPCODE_POWER in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    DEVICE_CLASS_POWER,
                    DPCODE_POWER,
                    json.loads(device.status_range.get(DPCODE_POWER).values).get(
                        "unit", 0
                    ),
                )
            )
        if DPCODE_VOLTAGE in device.status:
            entities.append(
                TuyaHaSensor(
                    device,
                    device_manager,
                    "Voltage",
                    DPCODE_VOLTAGE,
                    json.loads(device.status_range.get(DPCODE_VOLTAGE).values).get(
                        "unit", 0
                    ),
                )
            )

    return entities


class TuyaHaSensor(TuyaHaDevice, SensorEntity):
    """Tuya Sensor Device."""

    def __init__(
        self,
        device: TuyaDevice,
        device_manager: TuyaDeviceManager,
        sensor_type: str,
        sensor_code: str,
        sensor_unit: str,
    ):
        """Init TuyaHaSensor."""
        self._type = sensor_type
        self._code = sensor_code
        self._unit = sensor_unit
        super().__init__(device, device_manager)

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return f"{super().unique_id}{self._code}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.tuya_device.name + "_" + self._type

    @property
    def state(self):
        """Return the state of the sensor."""
        __value = self.tuya_device.status.get(self._code)
        if self.tuya_device.status_range.get(self._code).type == "Integer":
            __value_range = json.loads(
                self.tuya_device.status_range.get(self._code).values
            )
            __state = (__value) * 1.0 / (10 ** __value_range.get("scale"))
            if __value_range.get("scale") == 0:
                return int(__state)
            return f"%.{__value_range.get('scale')}f" % __state
        return ""

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Device class of this entity."""
        return self._type

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return True
