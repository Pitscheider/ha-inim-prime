from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory
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


def create_partition_device_info(
        entry: InimPrimeConfigEntry,
        partition_id: int,
        partition_name: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{entry.runtime_data.serial_number}_partition_{partition_id}")},
        name = f"Partition {partition_name}",
        model = "Prime Partition",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, entry.runtime_data.serial_number),
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
            entry: InimPrimeConfigEntry,
            partition: UnifiedPartition,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_partition_{self.partition_id}_state"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.label,
        )

    @property
    def native_value(self) -> str | None:
        partition = self.coordinator.gateway.get_partition(self.partition_id)
        if partition and partition.partition_state is not None:
            return partition.partition_state.name
        return None


class PartitionArmingStatusSelect(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SelectEntity,
):
    _attr_name = "Mode"
    _attr_icon = "mdi:shield-lock"
    _attr_options = [mode.name for mode in UnifiedArmingStatus]

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
            partition: UnifiedPartition
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_partition_{self.partition_id}_mode"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.label,
        )

    @property
    def current_option(self) -> str | None:
        """Return the current partition arming_status."""
        partition = self.coordinator.gateway.get_partition(self.partition_id)
        if partition and partition.arming_status is not None:
            return partition.arming_status.name
        return None

    async def async_select_option(self, option: str) -> None:
        """Set a new partition arming_status."""
        await self.coordinator.gateway.set_partition_arming_status(
            partition_id = self.partition_id,
            arming_status = UnifiedArmingStatus[option],
        )
        await self.coordinator.async_request_refresh()


class ResetPartitionMemoryButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Clear Alarm Memory"
    _attr_icon = "mdi:alarm-light-off"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
            partition: UnifiedPartition,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_partition_{self.partition_id}_clear_alarm_memory"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.label,
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
            entry: InimPrimeConfigEntry,
            partition: UnifiedPartition
    ):
        super().__init__(coordinator)

        self.partition_id = partition.partition_id
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_partition_{self.partition_id}_alarm_memory"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.label,
        )

    @property
    def is_on(self) -> bool | None:
        partition = self.coordinator.gateway.get_partition(self.partition_id)
        if partition:
            return partition.alarm_memory
        return None
