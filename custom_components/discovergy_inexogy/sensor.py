from __future__ import annotations

import logging
from datetime import timedelta

import requests
import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
    CONF_SCAN_INTERVAL,
    UnitOfPower,
    UnitOfEnergy,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_METERS = "meters"
CONF_METER_ID = "id"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_METERS): vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_METER_ID): cv.string,
                        vol.Required(CONF_NAME): cv.string,
                    }
                )
            ],
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Inexogy/Discovergy meter sensors from YAML."""
    token = config[CONF_TOKEN]
    meters = config[CONF_METERS]
    scan_interval = config[CONF_SCAN_INTERVAL]

    entities = []

    for meter_conf in meters:
        meter_id = meter_conf[CONF_METER_ID]
        name = meter_conf[CONF_NAME]

        entities.append(
            InexogyPowerSensor(
                token=token,
                meter_id=meter_id,
                name=f"{name} Power",
                scan_interval=scan_interval,
            )
        )
        entities.append(
            InexogyEnergyImportSensor(
                token=token,
                meter_id=meter_id,
                name=f"{name} Energy Import",
                scan_interval=scan_interval,
            )
        )
        entities.append(
            InexogyEnergyExportSensor(
                token=token,
                meter_id=meter_id,
                name=f"{name} Energy Export",
                scan_interval=scan_interval,
            )
        )

    add_entities(entities, update_before_add=True)


class InexogyBaseSensor(SensorEntity):
    """Base class for Inexogy meter sensors."""

    _attr_should_poll = True

    def __init__(self, token, meter_id, name, scan_interval):
        self._token = token
        self._meter_id = meter_id
        self._attr_name = name
        self._attr_unique_id = f"inexogy_{meter_id}_{self.__class__.__name__.lower()}"
        self._scan_interval = scan_interval
        self._last_data = None

    @property
    def extra_state_attributes(self):
        return {
            "meter_id": self._meter_id,
        }

    def _fetch_latest_reading(self):
        """Fetch latest reading from Inexogy/Discovergy API.

        HINWEIS:
        - Passe die URL und Feldnamen an deine tatsächliche API an.
        - Für Discovergy ist die Basis-API-Doku gut dokumentiert;
          Inexogy ist meist API-kompatibel.
        """

        url = f"https://api.inexogy.com/public/v1/meters/{self._meter_id}/readings?last=1"
        headers = {
            "Authorization": f"Token token={self._token}",
            "Accept": "application/json",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Erwartete Struktur: Liste mit einem Eintrag
            if isinstance(data, list) and data:
                self._last_data = data[0]
            else:
                _LOGGER.warning("Unerwartete Antwortstruktur von Inexogy: %s", data)
        except Exception as err:
            _LOGGER.error("Fehler beim Abrufen von Inexogy-Daten: %s", err)

    def update(self):
        """Update sensor state."""
        self._fetch_latest_reading()


class InexogyPowerSensor(InexogyBaseSensor):
    """Momentanleistung in W."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def update(self):
        super().update()
        if not self._last_data:
            return

        # Beispiel: data["values"]["power"]
        values = self._last_data.get("values", {})
        power = values.get("power")
        if power is not None:
            # Manche APIs liefern W direkt, ggf. Umrechnung vornehmen
            self._attr_native_value = float(power)


class InexogyEnergyImportSensor(InexogyBaseSensor):
    """Kumulierte Bezugsenergie in Wh oder kWh."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def update(self):
        super().update()
        if not self._last_data:
            return

        values = self._last_data.get("values", {})
        # Platzhalterfeldname, an API anpassen:
        energy_import = values.get("energyImport")
        if energy_import is not None:
            # Angenommen, API liefert Wh → in kWh umrechnen
            self._attr_native_value = float(energy_import) / 1000.0


class InexogyEnergyExportSensor(InexogyBaseSensor):
    """Kumulierte Einspeiseenergie in Wh oder kWh."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def update(self):
        super().update()
        if not self._last_data:
            return

        values = self._last_data.get("values", {})
        # Platzhalterfeldname, an API anpassen:
        energy_export = values.get("energyExport")
        if energy_export is not None:
            self._attr_native_value = float(energy_export) / 1000.0
