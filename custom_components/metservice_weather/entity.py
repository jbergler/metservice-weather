"""Base entity for MetService weather integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import WeatherUpdateCoordinator

_PUBLIC_MODEL = "MetService Public API"
_APP_MODEL = "MetService App API"
_CONFIGURATION_URL = "https://www.metservice.com"

_MARINE_REGION_NAMES: dict[str, str] = {
    "northland": "Northland",
    "great-barrier": "Great Barrier",
    "piha": "Piha",
    "coromandel": "Coromandel",
    "east-auckland": "Auckland East Coast",
    "west-auckland": "Auckland West Coast",
    "raglan": "Raglan",
    "bay-of-plenty": "Bay of Plenty",
    "rotorua-taupo": "Rotorua and Taupo",
    "gisborne-mahia": "Gisborne Mahia",
    "taranaki": "Taranaki",
    "whanganui-manawatu": "Manawatu-Whanganui",
    "hawke-bay-wairarapa": "Hawke Bay and Wairarapa",
    "kapiti-wellington": "Kapiti and Wellington",
    "nelson": "Nelson",
    "west-coast-north": "Buller and Westland",
    "kaikoura": "Kaikoura",
    "christchurch": "Canterbury",
    "west-coast-south": "Fiordland",
    "dunedin": "Otago",
    "southland": "Southland",
    "chatham-islands": "Chatham Islands",
}


def _marine_device_name(region_slug: str, location_name: str) -> str:
    """Derive the marine device's display name."""
    if not region_slug:
        return f"{location_name} Marine"
    label = _MARINE_REGION_NAMES.get(region_slug)
    if label is None:
        words = region_slug.replace("-", " ").replace("_", " ").split()
        label = " ".join(word.capitalize() for word in words) if words else None
    return label if label else f"{location_name} Marine"


def _model(coordinator: WeatherUpdateCoordinator) -> str:
    """Name the MetService API the device's data comes from."""
    return _APP_MODEL if coordinator.follows_ha_location else _PUBLIC_MODEL


def _location_device_name(coordinator: WeatherUpdateCoordinator) -> str:
    """Verbatim MetService location label for the town/rural device.

    A device that follows Home Assistant's location keeps the configured name
    rather than taking whichever place it happened to be set up in.
    """
    if coordinator.follows_ha_location:
        return coordinator.location_name
    data = coordinator.data
    if data is not None and getattr(data, "location_name", None):
        return data.location_name
    return coordinator.location_name


@callback
def async_register_location_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: WeatherUpdateCoordinator,
) -> str:
    """Register the town/rural location device and return its registry id."""
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.location)},
        name=_location_device_name(coordinator),
        manufacturer=MANUFACTURER,
        model=_model(coordinator),
        configuration_url=_CONFIGURATION_URL,
    )
    return device.id


class MetServiceEntity(CoordinatorEntity[WeatherUpdateCoordinator]):
    """Base class providing shared DeviceInfo for all MetService entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: WeatherUpdateCoordinator, device: str = "location"
    ) -> None:
        """Attach the appropriate MetService device info to the entity."""
        super().__init__(coordinator)
        location_label = _location_device_name(coordinator)
        if device == "marine":
            device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{coordinator.location}_marine")},
                name=_marine_device_name(
                    coordinator.marine_region_slug, location_label
                ),
                manufacturer=MANUFACTURER,
                model=_model(coordinator),
                configuration_url=_CONFIGURATION_URL,
            )
            if coordinator.location_device_id is not None:
                device_info["via_device_id"] = coordinator.location_device_id
            self._attr_device_info = device_info
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.location)},
                name=location_label,
                manufacturer=MANUFACTURER,
                model=_model(coordinator),
                configuration_url=_CONFIGURATION_URL,
            )
