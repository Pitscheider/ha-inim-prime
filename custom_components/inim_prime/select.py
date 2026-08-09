from .entities.partition import PartitionArmingStatusSelect
from .runtime_data import InimPrimeConfigEntry


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):
    partitions_coordinator = entry.runtime_data.coordinators.partitions

    entities = []

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(PartitionArmingStatusSelect(partitions_coordinator, partition))

    async_add_entities(entities, update_before_add = True)
