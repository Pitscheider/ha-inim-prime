from .models.system_faults import UNIFIED_EXPOSED_SYSTEM_FAULTS
from .coordinators import InimPrimeZonesUpdateCoordinator, InimPrimePartitionsUpdateCoordinator, InimPrimeSystemFaultsUpdateCoordinator
from .const import DOMAIN, ZONES_COORDINATOR, PARTITIONS_COORDINATOR, SYSTEM_FAULTS_COORDINATOR
from .entities.panel import SystemFaultBinarySensor
from .entities.partition import PartitionAlarmMemoryBinarySensor
from .entities.zone import ZoneStateBinarySensor, ZoneAlarmMemoryBinarySensor


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up INIM Prime binary sensors from a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]
    zones_coordinator: InimPrimeZonesUpdateCoordinator = coordinators[ZONES_COORDINATOR]
    partitions_coordinator: InimPrimePartitionsUpdateCoordinator = coordinators[PARTITIONS_COORDINATOR]
    system_faults_coordinator: InimPrimeSystemFaultsUpdateCoordinator = coordinators[SYSTEM_FAULTS_COORDINATOR]

    entities = []

    for zone in zones_coordinator.gateway.zones.values():
        entities.append(ZoneStateBinarySensor(zones_coordinator, entry, zone))
        entities.append(ZoneAlarmMemoryBinarySensor(zones_coordinator, entry, zone))

    for partition in partitions_coordinator.gateway.partitions.values():
        entities.append(PartitionAlarmMemoryBinarySensor(partitions_coordinator, entry, partition))

    for exposedSystemFault in UNIFIED_EXPOSED_SYSTEM_FAULTS:
        entities.append(
            SystemFaultBinarySensor(system_faults_coordinator, entry, exposedSystemFault)
        )

    async_add_entities(entities, update_before_add = True)
