from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..coordinators import InimPrimeGSMUpdateCoordinator
from ..const import DOMAIN, INIM_PRIME_DEVICE_MANUFACTURER
from ..runtime_data import InimPrimeConfigEntry


def create_gsm_device_info(
        entry: InimPrimeConfigEntry,
        domain: str = DOMAIN,
        sw_version: str | None = None
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{entry.runtime_data.serial_number}_gsm")},
        name = "GSM",
        model = "Prime GSM",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, entry.runtime_data.serial_number),
        sw_version = sw_version,
    )


class GSMSupplyVoltageSensor(
    CoordinatorEntity[InimPrimeGSMUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Supply Voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(
            self,
            coordinator: InimPrimeGSMUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_gsm_supply_voltage"

        self._attr_device_info = create_gsm_device_info(
            entry = entry,
            sw_version = self.coordinator.data.firmware_version,
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.gateway.gsm.supply_voltage


class GSMOperatorSensor(
    CoordinatorEntity[InimPrimeGSMUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Operator"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:cellphone-wireless"

    def __init__(
            self,
            coordinator: InimPrimeGSMUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_gsm_operator"

        self._attr_device_info = create_gsm_device_info(
            entry = entry,
            sw_version = self.coordinator.data.firmware_version
        )

    @property
    def native_value(self) -> str | None:
        return self.coordinator.gateway.gsm.operator



class GSMSignalStrengthSensor(
    CoordinatorEntity[InimPrimeGSMUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Signal Strength"
    _attr_icon = "mdi:signal"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
            self,
            coordinator: InimPrimeGSMUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_gsm_signal_strength"

        self._attr_device_info = create_gsm_device_info(
            entry = entry,
            sw_version = self.coordinator.data.firmware_version,
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.gateway.gsm.signal_strength


class GSMCreditSensor(
    CoordinatorEntity[InimPrimeGSMUpdateCoordinator],
    SensorEntity,
):
    _attr_name = "Credit"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:cash-multiple"

    def __init__(
            self,
            coordinator: InimPrimeGSMUpdateCoordinator,
            entry: InimPrimeConfigEntry,
    ):
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.runtime_data.serial_number}_gsm_credit"

        self._attr_device_info = create_gsm_device_info(
            entry = entry,
            sw_version = self.coordinator.data.firmware_version,
        )

    @property
    def native_value(self) -> str | None:
        return self.coordinator.gateway.gsm.credit
