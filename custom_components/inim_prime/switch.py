from .entities.zone import ZoneBypassSwitch
from .runtime_data import InimPrimeConfigEntry

async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):

    zones_coordinator = entry.runtime_data.coordinators.zones

    entities = []

    if zones_coordinator is not None:
        for zone in zones_coordinator.gateway.zones.values():
            entities.append(ZoneBypassSwitch(zones_coordinator, entry, zone))

    async_add_entities(entities, update_before_add = True)
