from .runtime_data import InimPrimeConfigEntry
from .models.system_faults import UNIFIED_EXPOSED_SYSTEM_FAULTS

from .entities.panel import SystemFaultBinarySensor
from .entities.partition import PartitionAlarmMemoryBinarySensor
from .entities.zone import ZoneStateBinarySensor, ZoneAlarmMemoryBinarySensor


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities) -> None:
    """Set up INIM Prime binary sensors from a config entry."""
    zones_coordinator = entry.runtime_data.coordinators.zones
    partitions_coordinator = entry.runtime_data.coordinators.partitions
    system_faults_coordinator = entry.runtime_data.coordinators.system_faults

    entities = []

    if zones_coordinator is not None:
        for zone in zones_coordinator.gateway.zones.values():
            entities.append(ZoneStateBinarySensor(zones_coordinator, zone))
            entities.append(ZoneAlarmMemoryBinarySensor(zones_coordinator, zone))

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(PartitionAlarmMemoryBinarySensor(partitions_coordinator, partition))

    if system_faults_coordinator is not None:
        for exposedSystemFault in UNIFIED_EXPOSED_SYSTEM_FAULTS:
            entities.append(
                SystemFaultBinarySensor(system_faults_coordinator, exposedSystemFault)
            )

    async_add_entities(entities, update_before_add = True)
