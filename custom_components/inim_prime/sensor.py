from .coordinators import (
    InimPrimeZonesUpdateCoordinator,
    InimPrimePartitionsUpdateCoordinator,
    InimPrimeGSMUpdateCoordinator,
    InimPrimeSystemFaultsUpdateCoordinator,
)
from .const import DOMAIN, ZONES_COORDINATOR, PARTITIONS_COORDINATOR, GSM_COORDINATOR, SYSTEM_FAULTS_COORDINATOR
from .entities.gsm import GSMSupplyVoltageSensor, GSMOperatorSensor, GSMSignalStrengthSensor, GSMCreditSensor
from .entities.panel import PanelSupplyVoltageSensor, BypassedZonesCountSensor, ZonesAlarmMemoryCountSensor, \
    PartitionsAlarmMemoryCountSensor
from .entities.partition import PartitionStateSensor
from .entities.zone import ZoneStateSensor


async def async_setup_entry(hass, entry, async_add_entities):
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    zones_coordinator: InimPrimeZonesUpdateCoordinator | None = coordinators.get(ZONES_COORDINATOR)
    partitions_coordinator: InimPrimePartitionsUpdateCoordinator | None = coordinators.get(PARTITIONS_COORDINATOR)
    gsm_coordinator: InimPrimeGSMUpdateCoordinator | None = coordinators.get(GSM_COORDINATOR)
    system_faults_coordinator: InimPrimeSystemFaultsUpdateCoordinator | None = coordinators.get(SYSTEM_FAULTS_COORDINATOR)

    entities = []

    if zones_coordinator is not None:
        for zone in zones_coordinator.gateway.zones.values():
            entities.append(ZoneStateSensor(zones_coordinator, entry, zone))

        entities.append(BypassedZonesCountSensor(zones_coordinator, entry))
        entities.append(ZonesAlarmMemoryCountSensor(zones_coordinator, entry))

    if partitions_coordinator is not None:
        for partition in partitions_coordinator.gateway.partitions.values():
            entities.append(PartitionStateSensor(partitions_coordinator, entry, partition))

        entities.append(PartitionsAlarmMemoryCountSensor(partitions_coordinator, entry))

    if system_faults_coordinator is not None:
        entities.append(PanelSupplyVoltageSensor(system_faults_coordinator, entry))

    if gsm_coordinator is not None:
        entities.append(GSMSupplyVoltageSensor(gsm_coordinator, entry))
        entities.append(GSMOperatorSensor(gsm_coordinator, entry))
        entities.append(GSMSignalStrengthSensor(gsm_coordinator, entry))
        entities.append(GSMCreditSensor(gsm_coordinator, entry))

    async_add_entities(entities, update_before_add = True)
