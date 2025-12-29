# Inexogy / Discovergy Smart Meter for Home Assistant

Dieses Custom Component bindet Inexogy/Discovergy Zähler als Sensoren in Home Assistant ein.

## Installation (HACS)

1. In HACS → Integrationen → Repository hinzufügen:
   - URL: `https://github.com/deinuser/ha-inexogy`
   - Typ: Integration
2. Installation ausführen
3. Home Assistant neu starten

## Konfiguration

In `configuration.yaml`:

```yaml
sensor:
  - platform: inexogy
    token: !secret inexogy_token
    meters:
      - id: "DE1234567890"
        name: "Hauszähler"
