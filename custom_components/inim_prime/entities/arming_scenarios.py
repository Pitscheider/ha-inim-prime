from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, INIM_PRIME_DEVICE_MANUFACTURER
from ..coordinators import InimPrimePartitionsUpdateCoordinator
from ..models.arming_scenarios import UnifiedArmingScenario


def create_arming_scenarios_device_info(
        serial_number: str,
        domain: str = DOMAIN,
) -> DeviceInfo:
    return DeviceInfo(
        identifiers = {(domain, f"{serial_number}_arming_scenarios")},
        name = "Arming Scenarios",
        model = "Prime Arming Scenarios",
        manufacturer = INIM_PRIME_DEVICE_MANUFACTURER,
        via_device = (domain, serial_number),
    )


class ArmingScenarioApplyButton(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    ButtonEntity,
):
    _attr_has_entity_name = True
    _attr_icon = "mdi:play-circle-outline"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            arming_scenario: UnifiedArmingScenario,
    ):
        super().__init__(coordinator)

        self.arming_scenario_id = arming_scenario.arming_scenario_id
        self._attr_name = arming_scenario.label
        self._attr_unique_id = f"{self.coordinator.serial_number}_arming_scenario_{self.arming_scenario_id}_apply"

        self._attr_device_info = create_arming_scenarios_device_info(
            serial_number = self.coordinator.serial_number,
        )

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.gateway.get_arming_scenario(self.arming_scenario_id) is not None
        )

    async def async_press(self) -> None:
        await self.coordinator.gateway.apply_arming_scenario(self.arming_scenario_id)
        await self.coordinator.async_request_refresh()


class ArmingScenarioActiveBinarySensor(
    CoordinatorEntity[InimPrimePartitionsUpdateCoordinator],
    BinarySensorEntity,
):
    _attr_has_entity_name = True
    _attr_icon = "mdi:shield-check-outline"

    def __init__(
            self,
            coordinator: InimPrimePartitionsUpdateCoordinator,
            arming_scenario: UnifiedArmingScenario,
    ):
        super().__init__(coordinator)

        self.arming_scenario_id = arming_scenario.arming_scenario_id
        self._attr_name = f"{arming_scenario.label} active"
        self._attr_unique_id = f"{self.coordinator.serial_number}_arming_scenario_{self.arming_scenario_id}_active"

        self._attr_device_info = create_arming_scenarios_device_info(
            serial_number = self.coordinator.serial_number,
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.gateway.is_arming_scenario_active(self.arming_scenario_id)