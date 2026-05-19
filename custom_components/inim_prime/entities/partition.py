from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..coordinators import InimPrimePartitionsUpdateCoordinator
from ..const import INIM_PRIME_DEVICE_MANUFACTURER, CONF_SERIAL_NUMBER, DOMAIN
from inim.prime.primelan.models.partition import (
    SetPartitionModeRequest,
    PartitionMode,
    ClearPartitionAlarmMemoryRequest,
    PartitionState,
    PartitionStatus,
)


def create_partition_device_info(
        entry: ConfigEntry,
        partition_id: int,
        partition_name: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{entry.data[CONF_SERIAL_NUMBER]}_partition_{partition_id}")},
        name = f"Partition {partition_name}",
        model = "Prime Partition",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, entry.data[CONF_SERIAL_NUMBER]),
    )


class PartitionStateSensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [state.name for state in PartitionState]
    _attr_icon = "mdi:magnify"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: ConfigEntry,
            partition: PartitionStatus,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_partition_{self.partition_id}_state"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.name,
        )

    @property
    def native_value(self) -> str | None:
        partition = self.coordinator.data.get(self.partition_id)
        if partition:
            return partition.state.name
        return None


class PartitionModeSelect(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SelectEntity,
):
    _attr_name = "Mode"
    _attr_icon = "mdi:shield-lock"
    _attr_options = [mode.name for mode in PartitionMode]

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: ConfigEntry,
            partition: PartitionStatus
    ):
        super().__init__(coordinator)

        self.partition_id = partition.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_partition_{self.partition_id}_mode"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.name,
        )

    @property
    def current_option(self) -> str | None:
        """Return the current partition mode."""
        partition = self.coordinator.data.get(self.partition_id)
        if partition:
            return partition.mode.name
        return None

    async def async_select_option(self, option: str) -> None:
        """Set a new partition mode."""
        mode = PartitionMode[option]

        request = SetPartitionModeRequest(
            partition_id = self.partition_id,
            mode = mode,
        )

        await self.coordinator.client.set_partition_mode(request)
        await self.coordinator.async_request_refresh()


class ClearPartitionAlarmMemoryButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Clear Alarm Memory"
    _attr_icon = "mdi:alarm-light-off"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: ConfigEntry,
            partition: PartitionStatus,
    ):
        super().__init__(coordinator)

        self.partition_id = partition.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_partition_{self.partition_id}_clear_alarm_memory"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.name,
        )

    async def async_press(self) -> None:
        request = ClearPartitionAlarmMemoryRequest(
            partition_id = self.partition_id,
        )

        await self.coordinator.client.clear_partition_alarm_memory(request)
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
            entry: ConfigEntry,
            partition: PartitionStatus
    ):
        super().__init__(coordinator)

        self.partition_id = partition.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_partition_{self.partition_id}_alarm_memory"

        self._attr_device_info = create_partition_device_info(
            entry = entry,
            partition_id = self.partition_id,
            partition_name = partition.name,
        )

    @property
    def is_on(self) -> bool | None:
        partition = self.coordinator.data.get(self.partition_id)
        if partition:
            return partition.alarm_memory
        return None
