from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelState, \
    AlarmControlPanelEntityFeature
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..runtime_data import InimPrimeConfigEntry
from ..models.partitions import (
    UnifiedPartitionState,
    UnifiedPartition,
    UnifiedArmingStatus,
)
from ..coordinators import InimPrimePartitionsUpdateCoordinator
from ..const import INIM_PRIME_DEVICE_MANUFACTURER, DOMAIN

_UNIFIED_ARMING_STATUS_TO_ALARM_CONTROL_PANEL_STATE: dict[UnifiedArmingStatus, AlarmControlPanelState] = {
    UnifiedArmingStatus.ARM_AWAY: AlarmControlPanelState.ARMED_AWAY,
    UnifiedArmingStatus.ARM_STAY: AlarmControlPanelState.ARMED_HOME,
    UnifiedArmingStatus.ARM_INSTANT: AlarmControlPanelState.ARMED_NIGHT,
    UnifiedArmingStatus.DISARMED: AlarmControlPanelState.DISARMED,
}


def create_partition_device_info(
        partition_id: int,
        partition_name: str,
        serial_number: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{serial_number}_partition_{partition_id}")},
        name = f"Partition {partition_name}",
        model = "Prime Partition",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, serial_number),
    )


class PartitionStateSensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [state.name for state in UnifiedPartitionState]
    _attr_icon = "mdi:magnify"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            partition: UnifiedPartition,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_partition_{self.partition_id}_state"

        self._attr_device_info = create_partition_device_info(
            partition_id = self.partition_id,
            partition_name = partition.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def native_value(self) -> str | None:
        partition = self.coordinator.gateway.get_partition(self.partition_id)
        if partition and partition.partition_state is not None:
            return partition.partition_state.name
        return None


class PartitionAlarmControlPanel(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    AlarmControlPanelEntity,
):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_options = [mode.name for mode in UnifiedArmingStatus]
    _attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            partition: UnifiedPartition
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_partition_{self.partition_id}_alarm_control_panel"
        self._optimistic_state: AlarmControlPanelState | None = None

        self._attr_device_info = create_partition_device_info(
            partition_id = self.partition_id,
            partition_name = partition.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def _partition(self) -> UnifiedPartition | None:
        return self.coordinator.gateway.get_partition(self.partition_id)

    @property
    def available(self) -> bool:
        return super().available and self._partition is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fresh panel data replaces any optimistic state."""
        self._optimistic_state = None
        super()._handle_coordinator_update()

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        if self._optimistic_state is not None:
            return self._optimistic_state

        partition = self._partition
        if partition is None or partition.arming_status is None:
            return None

        if partition.partition_state in (UnifiedPartitionState.ALARM, UnifiedPartitionState.TAMPER):
            return AlarmControlPanelState.TRIGGERED

        return _UNIFIED_ARMING_STATUS_TO_ALARM_CONTROL_PANEL_STATE[partition.arming_status]

    @property
    def extra_state_attributes(self) -> dict | None:
        partition = self._partition
        if partition is None:
            return None
        return {
            "partition_id": partition.partition_id,
        }

    async def _async_set(
            self,
            arming_status: UnifiedArmingStatus,
            optimistic: AlarmControlPanelState,
    ) -> None:
        try:
            await self.coordinator.gateway.set_partition_arming_status(
                partition_id = self.partition_id,
                arming_status = arming_status,
            )
        except Exception as err:
            raise HomeAssistantError(
                f"Could not set {arming_status.name} on partition {self.partition_id}: {err}"
            ) from err

        # Show the result immediately; the refresh below confirms or corrects it.
        self._optimistic_state = optimistic
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._async_set(UnifiedArmingStatus.DISARMED, AlarmControlPanelState.DISARMED)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._async_set(UnifiedArmingStatus.ARM_AWAY, AlarmControlPanelState.ARMED_AWAY)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._async_set(UnifiedArmingStatus.ARM_STAY, AlarmControlPanelState.ARMED_HOME)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._async_set(UnifiedArmingStatus.ARM_INSTANT, AlarmControlPanelState.ARMED_NIGHT)

class ResetPartitionMemoryButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Reset Memory"
    _attr_icon = "mdi:alarm-light-off"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            partition: UnifiedPartition,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_partition_{self.partition_id}_reset_memory"

        self._attr_device_info = create_partition_device_info(
            partition_id = self.partition_id,
            partition_name = partition.label,
            serial_number = self.coordinator.serial_number,
        )

    async def async_press(self) -> None:

        await self.coordinator.gateway.reset_partition_memory(
            partition_id = self.partition_id,
        )
        await self.coordinator.async_request_refresh()


class PartitionAlarmMemoryBinarySensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alarm-light"
    _attr_name = "Alarm Memory"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            partition: UnifiedPartition
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_partition_{self.partition_id}_alarm_memory"

        self._attr_device_info = create_partition_device_info(
            partition_id = self.partition_id,
            partition_name = partition.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def is_on(self) -> bool | None:
        partition = self.coordinator.gateway.get_partition(self.partition_id)
        if partition:
            return partition.alarm_memory
        return None
