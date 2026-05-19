from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..coordinators import InimPrimeZonesUpdateCoordinator
from ..const import INIM_PRIME_DEVICE_MANUFACTURER, CONF_SERIAL_NUMBER, DOMAIN
from inim.prime.primelan.models.zone import ZoneState, ZoneStatus, ZoneExclusionSetRequest


def create_zone_device_info(
        entry: ConfigEntry,
        zone_id: int,
        zone_name: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{entry.data[CONF_SERIAL_NUMBER]}_zone_{zone_id}")},
        name = f"Zone {zone_name}",
        model = "Prime Zone",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, entry.data[CONF_SERIAL_NUMBER]),
    )


class ZoneStateBinarySensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_name = None

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: ConfigEntry,
            zone: ZoneStatus,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_zone_{self.zone_id}_triggered"

        self._attr_device_info = create_zone_device_info(
            entry = entry,
            zone_id = self.zone_id,
            zone_name = zone.name,
        )

    @property
    def is_on(self) -> bool | None:
        zone = self.coordinator.data.get(self.zone_id)

        if zone:
            if zone.state == ZoneState.ALARM:
                return True
            if zone.state == ZoneState.READY:
                return False
        return None


class ZoneStateSensor(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [state.name for state in ZoneState]
    _attr_icon = "mdi:magnify"

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: ConfigEntry,
            zone: ZoneStatus,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_zone_{self.zone_id}_state"

        self._attr_device_info = create_zone_device_info(
            entry = entry,
            zone_id = self.zone_id,
            zone_name = zone.name,
        )

    @property
    def native_value(self) -> str | None:
        zone = self.coordinator.data.get(self.zone_id)
        if zone:
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
            entry: ConfigEntry,
            zone: ZoneStatus,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_zone_{self.zone_id}_alarm_memory"

        self._attr_device_info = create_zone_device_info(
            entry = entry,
            zone_id = self.zone_id,
            zone_name = zone.name,
        )

    @property
    def is_on(self) -> bool | None:
        zone = self.coordinator.data.get(self.zone_id)
        if zone:
            return zone.alarm_memory
        return None


class ZoneExclusionSwitch(
    CoordinatorEntity[InimPrimeZonesUpdateCoordinator],
    SwitchEntity,
):
    _attr_name = "Exclusion"
    _attr_icon = "mdi:cancel"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
            self,
            coordinator: InimPrimeZonesUpdateCoordinator,
            entry: ConfigEntry,
            zone: ZoneStatus,
    ):
        super().__init__(coordinator)

        self.zone_id = zone.id
        self._attr_unique_id = f"{entry.data[CONF_SERIAL_NUMBER]}_zone_{self.zone_id}_exclusion"

        self._attr_device_info = create_zone_device_info(
            entry = entry,
            zone_id = self.zone_id,
            zone_name = zone.name,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if zone is excluded (switch ON = excluded)."""
        zone = self.coordinator.data.get(self.zone_id)
        if zone:
            return zone.excluded
        return None

    async def async_turn_on(self, **kwargs):
        """Set zone as excluded."""
        request = ZoneExclusionSetRequest(zone_id = self.zone_id, exclude = True)
        await self.coordinator.client.set_zone_exclusion(request)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Set zone as included."""
        request = ZoneExclusionSetRequest(zone_id = self.zone_id, exclude = False)
        await self.coordinator.client.set_zone_exclusion(request)
        await self.coordinator.async_request_refresh()
