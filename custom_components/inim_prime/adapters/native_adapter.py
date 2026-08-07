"""Adapter that exposes inim.prime.native.Client through the unified interface.

Only wraps what the native gateway currently supports: zones (status +
bypass), partitions (status + arming + alarm-memory reset), and outputs
(on/off only, no dimming). GSM, system faults, log events and scenarios are
not implemented in the native library yet, so this adapter simply has no
methods for them -- InimPrimeGateway is what decides whether those features
are available at all (gated on whether PrimelanAdapter is configured).
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Optional

from inim.prime.native.client import Client as NativeClient
from inim.prime.native.models.partitions import (
    ArmingStatus as NativeArmingStatus,
    Partition as NativePartition,
    PartitionState as NativePartitionState,
)
from inim.prime.native.models.outputs import (
    Output as NativeOutput,
)
from inim.prime.native.models.zones import (
    Zone as NativeZone,
    ZoneState as NativeZoneState,
)
from ..models.outputs import (
    UnifiedOutput,
)
from ..models.partitions import (
    UnifiedArmingStatus,
    UnifiedPartition,
    UnifiedPartitionState,
)
from ..models.zones import (
    UnifiedZoneState,
    UnifiedZone,
)


_ZONE_STATE_MAP: dict[NativeZoneState, UnifiedZoneState] = {
    NativeZoneState.STANDBY: UnifiedZoneState.STANDBY,
    NativeZoneState.ALARM: UnifiedZoneState.ALARM,
    NativeZoneState.TAMPER: UnifiedZoneState.TAMPER,
    NativeZoneState.SHORT_CIRCUIT: UnifiedZoneState.SHORT_CIRCUIT,
}

_PARTITION_STATE_MAP: dict[NativePartitionState, UnifiedPartitionState] = {
    NativePartitionState.OK: UnifiedPartitionState.OK,
    NativePartitionState.ALARM: UnifiedPartitionState.ALARM,
    NativePartitionState.TAMPER: UnifiedPartitionState.TAMPER,
}

_ARMING_STATUS_MAP: dict[NativeArmingStatus, UnifiedArmingStatus] = {
    NativeArmingStatus.ARM_AWAY: UnifiedArmingStatus.ARM_AWAY,
    NativeArmingStatus.ARM_STAY: UnifiedArmingStatus.ARM_STAY,
    NativeArmingStatus.ARM_INSTANT: UnifiedArmingStatus.ARM_INSTANT,
    NativeArmingStatus.DISARMED: UnifiedArmingStatus.DISARMED,
}
_UNIFIED_ARMING_STATUS_MAP: dict[UnifiedArmingStatus, NativeArmingStatus] = {v: k for k, v in _ARMING_STATUS_MAP.items()}


def _zone_to_unified(zone: NativeZone) -> UnifiedZone:
    unified_zone: UnifiedZone

    if zone.zone_status is None:
        unified_zone = UnifiedZone(
            zone_id = zone.zone_id,
            label = zone.label,
            partitions = zone.zone_setting.partitions,
            state = None,
            bypass = None,
            alarm_memory = None,
        )
    else:
        unified_zone = UnifiedZone(
            zone_id = zone.zone_id,
            label = zone.label,
            partitions = zone.zone_setting.partitions,
            state = _ZONE_STATE_MAP[zone.zone_status.state],
            bypass = zone.zone_status.bypass,
            alarm_memory = zone.zone_status.alarm_memory,
        )

    return unified_zone


def _partition_to_unified(partition: NativePartition) -> UnifiedPartition:
    unified_partition: UnifiedPartition

    if partition.status is None:
        unified_partition = UnifiedPartition(
            partition_id = partition.partition_id,
            label = partition.label,
            zones = partition.zones,
            arming_status = None,
            partition_state = None,
            alarm_memory = None,
        )
    else:
        unified_partition = UnifiedPartition(
            partition_id = partition.partition_id,
            label = partition.label,
            zones = partition.zones,
            arming_status = _ARMING_STATUS_MAP[partition.status.arming_status],
            partition_state = _PARTITION_STATE_MAP[partition.status.partition_state],
            alarm_memory = partition.status.alarm_memory,
        )

    return unified_partition

def _output_to_unified(output: NativeOutput) -> UnifiedOutput:
    unified_output: UnifiedOutput

    if output.output_status is None:
        unified_output = UnifiedOutput(
            output_id = output.terminal_id,
            label = output.label,
            state = None,
        )
    else:
        unified_output = UnifiedOutput(
            output_id = output.terminal_id,
            label = output.label,
            state = output.output_status.state,
        )
    return unified_output


class NativeAdapter:
    """Wraps a connected inim.prime.native.Client instance."""
    __slots__ = (
        "_client",
        "_zones",
        "_partitions",
        "_outputs",
    )

    def __init__(self, client: NativeClient) -> None:
        self._client = client

        self._zones: dict[int, UnifiedZone] = {}
        self._partitions: dict[int, UnifiedPartition] = {}
        self._outputs: dict[int, UnifiedOutput] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        await self._client.connect()
        await self._client.ensure_initialized()

    async def close(self) -> None:
        self._client.disconnect()

    @property
    def serial_number(self) -> Optional[str]:
        info = self._client.panel_info
        return info[0] if info else None


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
    def outputs(self) -> MappingProxyType[int, UnifiedOutput]:
        return MappingProxyType[int, UnifiedOutput](self._outputs)

    @property
    def count_bypassed_zones(self) -> int:
        return sum(1 for zone in self._zones.values() if zone.bypass == True)

    @property
    def count_zone_alarm_memories(self) -> int:
        return sum(1 for zone in self._zones.values() if zone.alarm_memory == True)


    def get_zone(self, zone_id: int) -> UnifiedZone | None:
        return self._zones.get(zone_id)

    def get_partition(self, partition_id: int) -> UnifiedPartition | None:
        return self._partitions.get(partition_id)

    # ------------------------------------------------------------------
    # Updaters
    # ------------------------------------------------------------------
    async def update_zones(self) -> MappingProxyType[int, UnifiedZone]:
        await self._client.update_zone_terminals()

        result: dict[int, UnifiedZone] = {}
        for zone_id, zone in self._client.zones.items():
            result[zone_id] = _zone_to_unified(zone)
        self._zones = result
        return self.zones

    async def update_partitions(self) -> MappingProxyType[int, UnifiedPartition]:
        native_partitions = await self._client.update_partitions()

        partitions: dict[int, UnifiedPartition] = {}
        for partition_id, partition in native_partitions.items():
            partitions[partition_id] = _partition_to_unified(partition)
        self._partitions = partitions
        return self.partitions

    async def update_outputs(self) -> MappingProxyType[int, UnifiedOutput]:
        native_outputs = await self._client.update_outputs()

        outputs: dict[int, UnifiedOutput] = {}
        for output_id, output in native_outputs.items():
            outputs[output_id] = _output_to_unified(output)
        self._outputs = outputs
        return self.outputs


    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    ### Zones
    async def set_zone_bypass(
            self,
            zone_id: int,
            bypass: bool
    ) -> None:
        await self._client.set_zone_bypass(zone_id, bypass)


    async def set_all_zone_bypasses(
            self,
            bypass: bool,
    ) -> None:
        """Set all zones bypass value. The native gateway changes only those which aren't currently in that state."""
        await self._client.set_all_zone_bypasses(bypass)

    ### Partition arming status
    async def set_partition_arming_statuses(
            self,
            arming_statuses: dict[int, UnifiedArmingStatus],
    ) -> None:
        native_arming_statuses: dict[int, NativeArmingStatus] = {}
        for partition_id, arming_status in arming_statuses.items():
            native_arming_statuses[partition_id] = _UNIFIED_ARMING_STATUS_MAP[arming_status]

        await self._client.set_partition_arming_statuses(native_arming_statuses)

    async def set_partition_arming_status(
            self,
            partition_id: int,
            arming_status: UnifiedArmingStatus
    ) -> None:
        native_arming_status = _UNIFIED_ARMING_STATUS_MAP[arming_status]
        await self._client.set_partition_arming_status(partition_id, native_arming_status)

    async def set_all_partitions_arming_status(
            self,
            arming_status: UnifiedArmingStatus,
    ) -> None:
        native_arming_status = _UNIFIED_ARMING_STATUS_MAP[arming_status]
        await self._client.set_all_partitions_arming_status(native_arming_status)

    ### Reset partition memory
    async def reset_partition_memories(
            self,
            partition_ids: set[int],
    ) -> None:
        await self._client.reset_partition_memories(partition_ids)

    async def reset_partition_memory(
            self,
            partition_id: int,
    ) -> None:
        await self._client.reset_partition_memory(partition_id)

    async def reset_all_partition_memories(self) -> None:
        await self._client.reset_all_partition_memories()

    ### Outputs
    async def set_output(
            self,
            output_id: int,
            state: bool
    ) -> None:
        await self._client.set_output(output_id, state)
