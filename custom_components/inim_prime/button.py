from .entities.panel import DisableAllZoneBypassesButton, ResetAllPartitionMemoriesButton
from .entities.partition import ResetPartitionMemoryButton
from .runtime_data import InimPrimeConfigEntry


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):

    partitions_coordinator = entry.runtime_data.coordinators.partitions
    zones_coordinator = entry.runtime_data.coordinators.zones

    entities = []

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(ResetPartitionMemoryButton(partitions_coordinator, entry, partition))

        entities.append(ResetAllPartitionMemoriesButton(partitions_coordinator, entry))

    if zones_coordinator is not None:
        entities.append(DisableAllZoneBypassesButton(zones_coordinator, entry))

    async_add_entities(entities, update_before_add = True)