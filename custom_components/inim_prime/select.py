from .coordinators import InimPrimePartitionsUpdateCoordinator
from .const import DOMAIN, PARTITIONS_COORDINATOR
from .entities.partition import PartitionArmingStatusSelect


async def async_setup_entry(hass, entry, async_add_entities):
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    partitions_coordinator: InimPrimePartitionsUpdateCoordinator = coordinators[PARTITIONS_COORDINATOR]

    entities = []

    for partition in partitions_coordinator.gateway.partitions.values():
        entities.append(PartitionArmingStatusSelect(partitions_coordinator, entry, partition))

    async_add_entities(entities, update_before_add = True)
