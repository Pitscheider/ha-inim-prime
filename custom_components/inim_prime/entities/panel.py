import asyncio

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.event import EventEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..custom_types import InimPrimeConfigEntry
from ..models.log_events import UnifiedLogEvent
from ..models.system_faults import UnifiedSystemFault
from ..const import INIM_PRIME_DEVICE_MANUFACTURER, DOMAIN
from ..coordinators import InimPrimePanelLogEventsCoordinator, InimPrimeSystemFaultsUpdateCoordinator, \
    InimPrimeZonesUpdateCoordinator, InimPrimePartitionsUpdateCoordinator


def create_panel_device_info(
        entry: InimPrimeConfigEntry,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, entry.runtime_data.serial_number)},
        name = "Inim Prime Panel",
        model = "Prime Panel",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        serial_number = entry.runtime_data.serial_number,
    )


SYSTEM_FAULT_NAMES: dict[UnifiedSystemFault, str] = {
    UnifiedSystemFault.LOW_BATTERY: "Low Battery",
    UnifiedSystemFault.NETWORK_FAULT: "Network Fault",
    UnifiedSystemFault.NO_TELEPHONE_LINE: "No Telephone Line",
    UnifiedSystemFault.RADIO_JAMMING: "Radio Jamming",
    UnifiedSystemFault.LOW_BATTERY_WIRELESS: "Wireless Device Low Battery",
    UnifiedSystemFault.WIRELESS_DEVICE_DISAPPEARANCE: "Wireless Device Missing",
    UnifiedSystemFault.GSM_FAULT: "GSM Fault",
    UnifiedSystemFault.SENSOR_DIRTY: "Sensor Dirty",
    UnifiedSystemFault.ZONE_FAULT: "Zone Fault",
    UnifiedSystemFault.SIRENS_FAULT: "Sirens Fault",
    UnifiedSystemFault.POWER_SUPPLY_FAULT: "Power Supply Fault",
    UnifiedSystemFault.RADIO_KEYBOARDS_FAULT: "Radio Keyboards Fault",
    UnifiedSystemFault.SABOTAGE_FAULT: "Sabotage",
    UnifiedSystemFault.INTERNET_FAULT: "Internet Fault",
}

SYSTEM_FAULT_ICONS: dict[UnifiedSystemFault, str] = {
    UnifiedSystemFault.LOW_BATTERY: "mdi:battery-alert",
    UnifiedSystemFault.NETWORK_FAULT: "mdi:lan-disconnect",
    UnifiedSystemFault.NO_TELEPHONE_LINE: "mdi:phone-off",
    UnifiedSystemFault.RADIO_JAMMING: "mdi:signal-off",
    UnifiedSystemFault.LOW_BATTERY_WIRELESS: "mdi:battery-alert-variant",
    UnifiedSystemFault.WIRELESS_DEVICE_DISAPPEARANCE: "mdi:access-point-off",
    UnifiedSystemFault.GSM_FAULT: "mdi:signal-off",
    UnifiedSystemFault.SENSOR_DIRTY: "mdi:spray",
    UnifiedSystemFault.ZONE_FAULT: "mdi:map-marker-alert",
    UnifiedSystemFault.SIRENS_FAULT: "mdi:alarm-light-outline",
    UnifiedSystemFault.POWER_SUPPLY_FAULT: "mdi:flash-alert",
    UnifiedSystemFault.RADIO_KEYBOARDS_FAULT: "mdi:keyboard-off",
    UnifiedSystemFault.SABOTAGE_FAULT: "mdi:alert-octagon",
    UnifiedSystemFault.INTERNET_FAULT: "mdi:web-off",
}


class SystemFaultBinarySensor(
    CoordinatorEntity[InimPrimeSystemFaultsUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
            self,
            coordinator: InimPrimeSystemFaultsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
            fault: UnifiedSystemFault,
    ):
        super().__init__(coordinator)

        self._fault = fault

        self._attr_name = SYSTEM_FAULT_NAMES.get(
            self._fault,
            self._fault.name.replace("_", " ").title()
        )

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_panel_system_fault_{self._fault.name.lower()}"

        self._attr_icon = SYSTEM_FAULT_ICONS.get(
            self._fault,
            "mdi:alert-circle",
        )

        self._attr_device_info = create_panel_device_info(entry)

    @property
    def is_on(self) -> bool:
        system_faults = self.coordinator.gateway.system_faults
        return system_faults.has_fault(self._fault)


class PanelSupplyVoltageSensor(
    CoordinatorEntity[InimPrimeSystemFaultsUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Supply Voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(
            self,
            coordinator: InimPrimeSystemFaultsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_panel_supply_voltage"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> float | None:
        """Return the supply voltage."""
        system_faults = self.coordinator.gateway.system_faults
        return system_faults.supply_voltage


class PanelLogEventsEvent(
    CoordinatorEntity[InimPrimePanelLogEventsCoordinator],
    EventEntity,
):
    _attr_name = "Log Events"
    _attr_event_types = ["generic"]

    def __init__(
            self,
            coordinator: InimPrimePanelLogEventsCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_panel_log_events"
        self._attr_device_info = create_panel_device_info(entry)

    async def handle_events(self, log_events: list[UnifiedLogEvent]) -> None:
        for log_event in log_events:
            self._trigger_event(
                event_type = "generic",
                event_attributes = {
                    "timestamp": log_event.timestamp.isoformat(),
                    "type": log_event.type,
                    "agent": log_event.agent,
                    "location": log_event.location,
                }
            )
            # Multiple events fired at the same time are only visible if self.async_write_ha_state() is triggered each time after waiting some time.
            self.async_write_ha_state()
            await asyncio.sleep(0.01)


class BypassedZonesCountSensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Bypassed Zones"
    _attr_icon = "mdi:cancel"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.runtime_data.serial_number}_bypassed_zones_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int:
        return self.coordinator.gateway.count_bypassed_zones


class DisableAllZoneBypassesButton(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Disable All Zone Bypasses"
    _attr_icon = "mdi:check-all"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_disable_all_zone_bypasses"

        self._attr_device_info = create_panel_device_info(
            entry = entry,
        )

    async def async_press(self) -> None:
        await self.coordinator.gateway.disable_all_zone_bypasses()
        await self.coordinator.async_request_refresh()


class ResetAllPartitionMemoriesButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Reset All Partition Memories"
    _attr_icon = "mdi:alarm-light-off"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_clear_all_partitions_alarm_memory"

        self._attr_device_info = create_panel_device_info(
            entry = entry,
        )

    async def async_press(self) -> None:
        await self.coordinator.gateway.reset_all_partition_memories()
        await self.coordinator.async_request_refresh()


class ZonesAlarmMemoryCountSensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Zones Alarm Memory"
    _attr_icon = "mdi:alarm-light"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_zones_alarm_memory_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int:
        return self.coordinator.gateway.count_zone_alarm_memories


class PartitionsAlarmMemoryCountSensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Partitions Alarm Memory"
    _attr_icon = "mdi:alarm-light"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_partitions_alarm_memory_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int:
        return self.coordinator.gateway.count_partition_alarm_memories
