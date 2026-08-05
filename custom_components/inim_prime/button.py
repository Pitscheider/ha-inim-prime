from .coordinators import InimPrimeZonesUpdateCoordinator, InimPrimePartitionsUpdateCoordinator
from .const import DOMAIN, ZONES_COORDINATOR, PARTITIONS_COORDINATOR
from .entities.panel import DisableAllZoneBypassesButton, ResetAllPartitionMemoriesButton
from .entities.partition import ResetPartitionMemoryButton


async def async_setup_entry(hass, entry, async_add_entities):
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    partitions_coordinator: InimPrimePartitionsUpdateCoordinator = coordinators[PARTITIONS_COORDINATOR]
    zones_coordinator: InimPrimeZonesUpdateCoordinator = coordinators[ZONES_COORDINATOR]

    entities = []

    for partition in partitions_coordinator.gateway.partitions.values():
        entities.append(ResetPartitionMemoryButton(partitions_coordinator, entry, partition))

    entities.append(DisableAllZoneBypassesButton(zones_coordinator, entry))
    entities.append(ResetAllPartitionMemoriesButton(partitions_coordinator, entry))

    async_add_entities(entities, update_before_add = True)