"""Adapter that exposes inim.prime.primelan.InimPrimeClient through the unified interface.

PrimeLAN is currently the only backend that can report GSM status, system
faults, log events, and output dimming -- those methods here have no native
counterpart, which is exactly why InimPrimeGateway gates their availability
on whether a PrimelanAdapter is configured at all.
"""
from __future__ import annotations

from types import MappingProxyType

from inim.prime.primelan.client import InimPrimeClient
from inim.prime.primelan.models.partition import (
    PartitionStatus as PrimelanPartitionStatus,
    ClearPartitionAlarmMemoryRequest,
    ArmingStatus as PrimelanArmingStatus,
    PartitionState as PrimelanPartitionState,
    SetPartitionArmingStatusRequest,
)
from inim.prime.primelan.models.system_faults import (
    SystemFault as PrimelanSystemFault,
    SystemFaultsStatus as PrimelanSystemFaultsStatus
)
from inim.prime.primelan.models.zone import (
    ZoneState as PrimelanZoneState,
    ZoneStatus as PrimelanZoneStatus,
    ZoneBypassSetRequest,
)
from ..models.gsm import (
    UnifiedGSM,
)
from ..models.log_events import (
    UnifiedLogEvent,
)
from ..models.partitions import (
    UnifiedPartitionState,
    UnifiedArmingStatus,
    UnifiedPartition,
)
from ..models.system_faults import (
    UnifiedSystemFaults,
    UnifiedSystemFault,
)
from ..models.zones import (
    UnifiedZoneState,
    UnifiedZone,
)

_ZONE_STATE_MAP: dict[PrimelanZoneState, UnifiedZoneState] = {
    PrimelanZoneState.TAMPER: UnifiedZoneState.TAMPER,
    PrimelanZoneState.STANDBY: UnifiedZoneState.STANDBY,
    PrimelanZoneState.ALARM: UnifiedZoneState.ALARM,
    PrimelanZoneState.SHORT_CIRCUIT: UnifiedZoneState.SHORT_CIRCUIT,
}

_PARTITION_STATE_MAP: dict[PrimelanPartitionState, UnifiedPartitionState] = {
    PrimelanPartitionState.OK: UnifiedPartitionState.OK,
    PrimelanPartitionState.ALARM: UnifiedPartitionState.ALARM,
    PrimelanPartitionState.TAMPER: UnifiedPartitionState.TAMPER,
}

_ARMING_STATUS_MAP: dict[PrimelanArmingStatus, UnifiedArmingStatus] = {
    PrimelanArmingStatus.ARM_AWAY: UnifiedArmingStatus.ARM_AWAY,
    PrimelanArmingStatus.ARM_STAY: UnifiedArmingStatus.ARM_STAY,
    PrimelanArmingStatus.ARM_INSTANT: UnifiedArmingStatus.ARM_INSTANT,
    PrimelanArmingStatus.DISARMED: UnifiedArmingStatus.DISARMED,
}
_UNIFIED_ARMING_STATUS_MAP: dict[UnifiedArmingStatus, PrimelanArmingStatus] = {v: k for k, v in _ARMING_STATUS_MAP.items()}

_SYSTEM_FAULT_MAP: dict[PrimelanSystemFault, UnifiedSystemFault] = {
    PrimelanSystemFault.RESERVED_0:                     UnifiedSystemFault.RESERVED_0,
    PrimelanSystemFault.RESERVED_1:                     UnifiedSystemFault.RESERVED_1,
    PrimelanSystemFault.LOW_BATTERY:                    UnifiedSystemFault.LOW_BATTERY,
    PrimelanSystemFault.NETWORK_FAULT:                  UnifiedSystemFault.NETWORK_FAULT,
    PrimelanSystemFault.NO_TELEPHONE_LINE:              UnifiedSystemFault.NO_TELEPHONE_LINE,
    PrimelanSystemFault.RADIO_JAMMING:                  UnifiedSystemFault.RADIO_JAMMING,
    PrimelanSystemFault.LOW_BATTERY_WIRELESS:           UnifiedSystemFault.LOW_BATTERY_WIRELESS,
    PrimelanSystemFault.WIRELESS_DEVICE_DISAPPEARANCE:  UnifiedSystemFault.WIRELESS_DEVICE_DISAPPEARANCE,
    PrimelanSystemFault.GSM_FAULT:                      UnifiedSystemFault.GSM_FAULT,
    PrimelanSystemFault.SENSOR_DIRTY:                   UnifiedSystemFault.SENSOR_DIRTY,
    PrimelanSystemFault.ZONE_FAULT:                     UnifiedSystemFault.ZONE_FAULT,
    PrimelanSystemFault.SIRENS_FAULT:                   UnifiedSystemFault.SIRENS_FAULT,
    PrimelanSystemFault.POWER_SUPPLY_FAULT:             UnifiedSystemFault.POWER_SUPPLY_FAULT,
    PrimelanSystemFault.RADIO_KEYBOARDS_FAULT:          UnifiedSystemFault.RADIO_KEYBOARDS_FAULT,
    PrimelanSystemFault.SABOTAGE_FAULT:                 UnifiedSystemFault.SABOTAGE_FAULT,
    PrimelanSystemFault.INTERNET_FAULT:                 UnifiedSystemFault.INTERNET_FAULT,
}

def _zone_to_unified(zone: PrimelanZoneStatus) -> UnifiedZone:
    unified_zone: UnifiedZone

    unified_zone = UnifiedZone(
        zone_id = zone.id,
        terminal_id = zone.terminal_id,
        label = zone.name,
        partitions = None,
        state = _ZONE_STATE_MAP[zone.state],
        bypass = zone.bypass,
        alarm_memory = zone.alarm_memory,
    )

    return unified_zone


def _partition_to_unified(partition: PrimelanPartitionStatus) -> UnifiedPartition:
    unified_partition: UnifiedPartition

    unified_partition = UnifiedPartition(
        partition_id = partition.id,
        label = partition.name,
        zones = None,
        arming_status = _ARMING_STATUS_MAP[partition.arming_status],
        partition_state = _PARTITION_STATE_MAP[partition.state],
        alarm_memory = partition.alarm_memory,
    )

    return unified_partition

class PrimelanAdapter:
    """Wraps a connected inim.prime.primelan.InimPrimeClient instance."""

    __slots__ = (
        "_client",
        "_zones",
        "_partitions",
        "_gsm",
        "_system_faults",
    )

    def __init__(self, client: InimPrimeClient) -> None:
        self._client = client

        self._zones: dict[int, UnifiedZone] = {}
        self._partitions: dict[int, UnifiedPartition] = {}
        self._gsm: UnifiedGSM | None = None
        self._system_faults: UnifiedSystemFaults | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        await self._client.connect()

    async def close(self) -> None:
        await self._client.close()

    # ------------------------------------------------------------------
    #   Properties
    # ------------------------------------------------------------------
    @property
    def zones(self) -> MappingProxyType[int, UnifiedZone]:
        return MappingProxyType[int, UnifiedZone](self._zones)

    @property
    def partitions(self) -> MappingProxyType[int, UnifiedPartition]:
        return MappingProxyType[int, UnifiedPartition](self._partitions)

    @property
    def gsm(self) -> UnifiedGSM | None:
        return self._gsm

    @property
    def system_faults(self) -> UnifiedSystemFaults | None:
        return self._system_faults

    @property
    def count_bypassed_zones(self) -> int:
        return sum(1 for zone in self._zones.values() if zone.bypass == True)

    @property
    def count_zone_alarm_memories(self) -> int:
        return sum(1 for zone in self._zones.values() if zone.alarm_memory == True)

    @property
    def count_partition_alarm_memories(self) -> int:
        return sum(1 for partition in self._partitions.values() if partition.alarm_memory == True)

    def get_zone(self, zone_id: int) -> UnifiedZone | None:
        return self._zones.get(zone_id)

    def get_partition(self, partition_id: int) -> UnifiedPartition | None:
        return self._partitions.get(partition_id)

    # ------------------------------------------------------------------
    # Updaters
    # ------------------------------------------------------------------
    async def update_zones(self) -> MappingProxyType[int, UnifiedZone]:
        primelan_zones = await self._client.get_zones_status()

        zones: dict[int, UnifiedZone] = {}
        for zone_id, zone in primelan_zones.items():
            zones[zone_id] = _zone_to_unified(zone)
        self._zones = zones
        return self.zones

    async def update_partitions(self) -> MappingProxyType[int, UnifiedPartition]:
        primelan_partitions = await self._client.get_partitions_status()

        partitions: dict[int, UnifiedPartition] = {}
        for partition_id, partition in primelan_partitions.items():
            partitions[partition_id] = _partition_to_unified(partition)
        self._partitions = partitions
        return self.partitions

    async def update_gsm(self) -> UnifiedGSM:
        primelan_gsm = await self._client.get_gsm_status()
        gsm = UnifiedGSM(
            supply_voltage = primelan_gsm.supply_voltage,
            firmware_version = primelan_gsm.firmware_version,
            operator = primelan_gsm.operator,
            signal_strength = primelan_gsm.signal_strength,
            credit = primelan_gsm.credit,
        )
        self._gsm = gsm
        return gsm

    async def update_system_faults(self) -> UnifiedSystemFaults:
        primelan_system_faults: PrimelanSystemFaultsStatus = await self._client.get_system_faults_status()
        faults: frozenset[PrimelanSystemFault] = primelan_system_faults.faults

        system_faults = UnifiedSystemFaults(
            supply_voltage = primelan_system_faults.supply_voltage,
            faults = frozenset[UnifiedSystemFault](
                _SYSTEM_FAULT_MAP[f] for f in faults if f in _SYSTEM_FAULT_MAP
            ),
        )
        self._system_faults = system_faults
        return system_faults

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    ### Zones
    async def set_zone_bypass(
            self,
            zone_id: int,
            bypass: bool
    ) -> None:
        if zone_id not in self._zones:
            raise KeyError(f"Unknown zone id: {zone_id}")

        await self._client.set_zone_bypass(
            ZoneBypassSetRequest(
                zone_id = zone_id,
                bypass = bypass
            )
        )

    async def set_all_zone_bypasses(
            self,
            bypass: bool,
    ) -> None:
        """Set all zones bypass value. The native gateway changes only those which aren't currently in that state."""
        for zone in self._zones.values():
            if zone.bypass is not None and zone.bypass == bypass:
                continue
            await self._client.set_zone_bypass(ZoneBypassSetRequest(
                zone_id = zone.zone_id,
                bypass = bypass,
            ))


    ### Partition arming status
    async def set_partition_arming_status(
            self,
            partition_id: int,
            arming_status: UnifiedArmingStatus
    ) -> None:
        if partition_id not in self._partitions:
            raise KeyError(f"Unknown partition id: {partition_id}")

        request = SetPartitionArmingStatusRequest(
            partition_id = partition_id,
            arming_status = _UNIFIED_ARMING_STATUS_MAP[arming_status],
        )
        await self._client.set_partition_mode(request)


    async def set_partition_arming_statuses(
            self,
            arming_statuses: dict[int, UnifiedArmingStatus],
    ) -> None:
        for partition_id, arming_status in arming_statuses.items():
            await self.set_partition_arming_status(partition_id, arming_status)


    async def set_all_partitions_arming_status(
            self,
            arming_status: UnifiedArmingStatus,
    ) -> None:
        for partition_id in self._partitions.keys():
            await self.set_partition_arming_status(partition_id, arming_status)


    ### Reset partition memory
    async def reset_partition_memory(
            self,
            partition_id: int,
    ) -> None:
        if partition_id not in self._partitions:
            raise KeyError(f"Unknown partition id: {partition_id}")

        request = ClearPartitionAlarmMemoryRequest(
            partition_id = partition_id,
        )
        await self._client.clear_partition_alarm_memory(request)

    async def reset_partition_memories(
            self,
            partition_ids: set[int],
    ) -> None:
        for partition_id in partition_ids:
            partition = self._partitions.get(partition_id)
            if partition is not None:
                if partition.alarm_memory is not None and partition.alarm_memory == False:
                    continue
                await self.reset_partition_memory(partition_id)


    async def reset_all_partition_memories(self) -> None:
        for partition in self._partitions.values():
            if partition.alarm_memory is not None and partition.alarm_memory == False:
                continue
            await self.reset_partition_memory(partition.partition_id)



    # ------------------------------------------------------------------
    # PrimeLAN-exclusive features
    # ------------------------------------------------------------------


    async def get_log_events(self, limit: int) -> list[UnifiedLogEvent]:
        events = await self._client.get_log_events(limit = limit)
        return [
            UnifiedLogEvent(
                id = event.id,
                timestamp = event.timestamp,
                type = event.type,
                agent = event.agent,
                location = event.location,
                value = event.value,
            )
            for event in events
        ]
