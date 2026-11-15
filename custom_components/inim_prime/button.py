from .entities.panel import DisableAllZoneBypassesButton, ResetAllPartitionMemoriesButton
from .entities.partition import ResetPartitionMemoryButton
from .entities.arming_scenarios import ArmingScenarioApplyButton
from .runtime_data import InimPrimeConfigEntry


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):

    partitions_coordinator = entry.runtime_data.coordinators.partitions
    zones_coordinator = entry.runtime_data.coordinators.zones
    gateway = entry.runtime_data.gateway

    entities = []

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(ResetPartitionMemoryButton(partitions_coordinator, partition))

        entities.append(ResetAllPartitionMemoriesButton(partitions_coordinator))

        if gateway.supports_arming_scenarios and gateway.arming_scenarios is not None:
            for arming_scenario in gateway.arming_scenarios.values():
                entities.append(ArmingScenarioApplyButton(partitions_coordinator, arming_scenario))

    if zones_coordinator is not None:
        entities.append(DisableAllZoneBypassesButton(zones_coordinator))

    async_add_entities(entities, update_before_add = True)