from .entities.partition import PartitionAlarmControlPanel
from .runtime_data import InimPrimeConfigEntry

# Arming is a panel write: one command in flight at a time.
PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):
    partitions_coordinator = entry.runtime_data.coordinators.partitions

    entities = []

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(PartitionAlarmControlPanel(partitions_coordinator, partition))

    async_add_entities(entities, update_before_add = True)