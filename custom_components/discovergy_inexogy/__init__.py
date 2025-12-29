from __future__ import annotations
from homeassistant.core import HomeAssistant

DOMAIN = "inexogy"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Inexogy integration via YAML."""
    # nichts weiter nötig fürs MVP
    return True
