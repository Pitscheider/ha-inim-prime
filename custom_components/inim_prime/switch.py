from .coordinators import InimPrimeZonesUpdateCoordinator
from .const import DOMAIN, ZONES_COORDINATOR
from .entities.zone import ZoneBypassSwitch


async def async_setup_entry(hass, entry, async_add_entities):
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    zones_coordinator: InimPrimeZonesUpdateCoordinator = coordinators[ZONES_COORDINATOR]

    entities = []

    for zone in zones_coordinator.gateway.zones.values():
        entities.append(ZoneBypassSwitch(zones_coordinator, entry, zone))

    async_add_entities(entities, update_before_add = True)
