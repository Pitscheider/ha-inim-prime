from .entities.gsm import GSMSupplyVoltageSensor, GSMOperatorSensor, GSMSignalStrengthSensor, GSMCreditSensor
from .entities.panel import PanelSupplyVoltageSensor, BypassedZonesCountSensor, ZonesAlarmMemoryCountSensor, \
    PartitionsAlarmMemoryCountSensor
from .entities.partition import PartitionStateSensor
from .entities.zone import ZoneStateSensor
from .runtime_data import InimPrimeConfigEntry


async def async_setup_entry(hass, entry: InimPrimeConfigEntry, async_add_entities):
    zones_coordinator = entry.runtime_data.coordinators.zones
    partitions_coordinator = entry.runtime_data.coordinators.partitions
    gsm_coordinator = entry.runtime_data.coordinators.gsm
    system_faults_coordinator = entry.runtime_data.coordinators.system_faults

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
