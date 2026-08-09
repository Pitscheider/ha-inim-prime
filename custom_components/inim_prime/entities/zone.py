from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import INIM_PRIME_DEVICE_MANUFACTURER, DOMAIN
from ..coordinators import InimPrimeZonesUpdateCoordinator
from ..models.zones import UnifiedZone, UnifiedZoneState


def create_zone_device_info(
        zone_id: int,
        zone_name: str,
        serial_number: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{serial_number}_zone_{zone_id}")},
        name = f"Zone {zone_name}",
        model = "Prime Zone",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, serial_number),
    )


class ZoneStateBinarySensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_name = None

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            zone: UnifiedZone,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.zone_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_zone_{self.zone_id}_triggered"

        self._attr_device_info = create_zone_device_info(
            zone_id = self.zone_id,
            zone_name = zone.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def is_on(self) -> bool | None:
        zone = self.coordinator.gateway.get_zone(self.zone_id)

        if zone and zone.state is not None:
            if zone.state == UnifiedZoneState.ALARM:
                return True
            if zone.state == UnifiedZoneState.STANDBY:
                return False
        return None


class ZoneStateSensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [state.name for state in UnifiedZoneState]
    _attr_icon = "mdi:magnify"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            zone: UnifiedZone,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.zone_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_zone_{self.zone_id}_state"

        self._attr_device_info = create_zone_device_info(
            zone_id = self.zone_id,
            zone_name = zone.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def native_value(self) -> str | None:
        zone = self.coordinator.gateway.get_zone(self.zone_id)
        if zone and zone.state is not None:
            return zone.state.name
        return None


class ZoneAlarmMemoryBinarySensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Alarm Memory"
    _attr_icon = "mdi:alarm-light"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            zone: UnifiedZone,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.zone_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_zone_{self.zone_id}_alarm_memory"

        self._attr_device_info = create_zone_device_info(
            zone_id = self.zone_id,
            zone_name = zone.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def is_on(self) -> bool | None:
        zone = self.coordinator.gateway.get_zone(self.zone_id)
        if zone:
            return zone.alarm_memory
        return None


class ZoneBypassSwitch(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SwitchEntity,
):
    _attr_name = "Bypass"
    _attr_icon = "mdi:cancel"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            zone: UnifiedZone,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.zone_id
        self._attr_unique_id = f"{self.coordinator.serial_number}_zone_{self.zone_id}_bypass"

        self._attr_device_info = create_zone_device_info(
            zone_id = self.zone_id,
            zone_name = zone.label,
            serial_number = self.coordinator.serial_number,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if zone is bypass (switch ON = bypass)."""
        zone = self.coordinator.gateway.get_zone(self.zone_id)
        if zone:
            return zone.bypass
        return None

    async def async_turn_on(self, **kwargs):
        """Set zone as bypassed."""
        await self.coordinator.gateway.set_zone_bypass(
            zone_id = self.zone_id,
            bypass = True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Set zone as not bypassed."""
        await self.coordinator.gateway.set_zone_bypass(
            zone_id = self.zone_id,
            bypass = False,
        )
        await self.coordinator.async_request_refresh()
