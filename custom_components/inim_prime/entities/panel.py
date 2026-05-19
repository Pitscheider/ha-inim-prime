import asyncio

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntity
from homeassistant.components.event import EventEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from inim.prime.primelan.helpers.partitions import clear_all_partitions_alarm_memory
from inim.prime.primelan.helpers.zones import include_all_zones
from inim.prime.primelan.models.log_event import LogEvent
from inim.prime.primelan.models.system_faults import SystemFault
from ..const import INIM_PRIME_DEVICE_MANUFACTURER, CONF_SERIAL_NUMBER, DOMAIN
from ..coordinators import InimPrimePanelLogEventsCoordinator, InimPrimeSystemFaultsUpdateCoordinator, \
    InimPrimeZonesUpdateCoordinator, InimPrimePartitionsUpdateCoordinator


def create_panel_device_info(
        entry: ConfigEntry,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, entry.data[CONF_SERIAL_NUMBER])},
        name = "Inim Prime Panel",
        model = "Prime Panel",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        serial_number = entry.data[CONF_SERIAL_NUMBER],
    )


SYSTEM_FAULT_NAMES: dict[SystemFault, str] = {
    SystemFault.LOW_BATTERY: "Low Battery",
    SystemFault.NETWORK_FAULT: "Network Fault",
    SystemFault.NO_TELEPHONE_LINE: "No Telephone Line",
    SystemFault.RADIO_JAMMING: "Radio Jamming",
    SystemFault.LOW_BATTERY_WIRELESS: "Wireless Device Low Battery",
    SystemFault.WIRELESS_DEVICE_DISAPPEARANCE: "Wireless Device Missing",
    SystemFault.GSM_FAULT: "GSM Fault",
    SystemFault.SENSOR_DIRTY: "Sensor Dirty",
    SystemFault.ZONE_FAULT: "Zone Fault",
    SystemFault.SIRENS_FAULT: "Sirens Fault",
    SystemFault.POWER_SUPPLY_FAULT: "Power Supply Fault",
    SystemFault.RADIO_KEYBOARDS_FAULT: "Radio Keyboards Fault",
    SystemFault.SABOTAGE_FAULT: "Sabotage",
    SystemFault.INTERNET_FAULT: "Internet Fault",
}

SYSTEM_FAULT_ICONS: dict[SystemFault, str] = {
    SystemFault.LOW_BATTERY: "mdi:battery-alert",
    SystemFault.NETWORK_FAULT: "mdi:lan-disconnect",
    SystemFault.NO_TELEPHONE_LINE: "mdi:phone-off",
    SystemFault.RADIO_JAMMING: "mdi:signal-off",
    SystemFault.LOW_BATTERY_WIRELESS: "mdi:battery-alert-variant",
    SystemFault.WIRELESS_DEVICE_DISAPPEARANCE: "mdi:access-point-off",
    SystemFault.GSM_FAULT: "mdi:signal-off",
    SystemFault.SENSOR_DIRTY: "mdi:spray",
    SystemFault.ZONE_FAULT: "mdi:map-marker-alert",
    SystemFault.SIRENS_FAULT: "mdi:alarm-light-outline",
    SystemFault.POWER_SUPPLY_FAULT: "mdi:flash-alert",
    SystemFault.RADIO_KEYBOARDS_FAULT: "mdi:keyboard-off",
    SystemFault.SABOTAGE_FAULT: "mdi:alert-octagon",
    SystemFault.INTERNET_FAULT: "mdi:web-off",
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
            entry: ConfigEntry,
            fault: SystemFault,
    ):
        super().__init__(coordinator)

        self._fault = fault

        self._attr_name = SYSTEM_FAULT_NAMES.get(
            self._fault,
            self._fault.name.replace("_", " ").title()
        )

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_panel_system_fault_{self._fault.name.lower()}"

        self._attr_icon = SYSTEM_FAULT_ICONS.get(
            self._fault,
            "mdi:alert-circle",
        )

        self._attr_device_info = create_panel_device_info(entry)

    @property
    def is_on(self) -> bool:
        system_faults = self.coordinator.data
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
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_panel_supply_voltage"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> float | None:
        """Return the supply voltage."""
        system_faults = self.coordinator.data
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
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_panel_log_events"
        self._attr_device_info = create_panel_device_info(entry)

    async def handle_events(self, log_events: list[LogEvent]) -> None:
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


class ExcludedZonesCountSensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Excluded Zones"
    _attr_icon = "mdi:cancel"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_excluded_zones_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data:
            return sum(zone.excluded for zone in self.coordinator.data.values())
        return None


class IncludeAllZonesButton(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Include All Zones"
    _attr_icon = "mdi:check-all"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_include_all_zones"

        self._attr_device_info = create_panel_device_info(
            entry = entry,
        )

    async def async_press(self) -> None:
        zones = await self.coordinator.client.get_zones_status()

        await include_all_zones(
            zones = zones,
            client = self.coordinator.client,
        )

        await self.coordinator.async_request_refresh()


class ClearAllPartitionsAlarmMemoryButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_name = "Clear All Alarm Memories"
    _attr_icon = "mdi:alarm-light-off"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_clear_all_partitions_alarm_memory"

        self._attr_device_info = create_panel_device_info(
            entry = entry,
        )

    async def async_press(self) -> None:
        partitions = await self.coordinator.client.get_partitions_status()

        await clear_all_partitions_alarm_memory(
            partitions = partitions,
            client = self.coordinator.client,
        )

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
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_zones_alarm_memory_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data:
            return sum(zone.alarm_memory for zone in self.coordinator.data.values())
        return None


class PartitionsAlarmMemoryCountSensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Partitions Alarm Memory"
    _attr_icon = "mdi:alarm-light"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            entry: ConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_partitions_alarm_memory_count"
        self._attr_device_info = create_panel_device_info(entry)

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data:
            return sum(partition.alarm_memory for partition in self.coordinator.data.values())
        return None
