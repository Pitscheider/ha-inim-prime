from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntry

from .entry_data import get_entry_data
from .const import (
    DOMAIN,
)
from .models.arming_scenarios import UnifiedArmingScenario
from .models.partitions import UnifiedPartition
from .models.zones import UnifiedZone
from .runtime_data import InimPrimeConfigEntry
from .gateway import InimPrimeGateway


###
### Serializers
###
def _hex(value: bytes | None) -> str | None:
    return value.hex(" ") if value is not None else None


def _zone_diagnostics(zone: UnifiedZone) -> dict[str, Any]:
    return {
        "zone_id": zone.zone_id,
        "terminal": zone.terminal_id,
        "label": zone.label,
        "state": zone.state.name if zone.state is not None else None,
        "bypass": zone.bypass,
        "alarm_memory": zone.alarm_memory,
        "native_status_bytes": _hex(zone.native_status_bytes),
        "native_state_str": zone.native_state_str,
    }


def _partition_diagnostics(partition: UnifiedPartition) -> dict[str, Any]:
    return {
        "partition_id": partition.partition_id,
        "label": partition.label,
        "partition_state": partition.partition_state.name if partition.partition_state is not None else None,
        "arming_status": partition.arming_status.name if partition.arming_status is not None else None,
        "alarm_memory": partition.alarm_memory,
    }


def _arming_scenario_diagnostics(
        gateway: InimPrimeGateway,
        arming_scenario: UnifiedArmingScenario,
) -> dict[str, Any]:
    targets: dict[int, dict[str, Any]] = {}
    for partition_id, target in arming_scenario.targets.items():
        partition = gateway.get_partition(partition_id)
        current = partition.arming_status if partition is not None else None
        targets[partition_id] = {
            "partition_label": partition.label if partition is not None else None,
            "target": target.name,
            "current": current.name if current is not None else None,
            "matches": current is target,
        }

    return {
        "arming_scenario_id": arming_scenario.arming_scenario_id,
        "label": arming_scenario.label,
        "active": gateway.is_arming_scenario_active(arming_scenario.arming_scenario_id),
        "targets": targets,
    }


###
### Diagnostics
###
async def async_get_config_entry_diagnostics(
        hass,
        entry: InimPrimeConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for the config entry."""

    gateway = entry.runtime_data.gateway
    data = get_entry_data(entry)

    diagnostics: dict[str, Any] = {
        "panel": {
            "serial_number": data["serial_number"],
            "backends_active": gateway.backends_active,
        },
        "zones": {
            zone_id: _zone_diagnostics(zone)
            for zone_id, zone in gateway.zones.items()
        },
        "partitions": {
            partition_id: _partition_diagnostics(partition)
            for partition_id, partition in gateway.partitions.items()
        },
    }

    arming_scenarios = gateway.arming_scenarios
    if arming_scenarios is not None:
        diagnostics["arming_scenarios"] = {
            arming_scenario_id: _arming_scenario_diagnostics(gateway, arming_scenario)
            for arming_scenario_id, arming_scenario in arming_scenarios.items()
        }

    system_faults = gateway.system_faults
    if system_faults is not None:
        diagnostics["system_faults"] = {
            "supply_voltage": system_faults.supply_voltage,
            "faults": [fault.name for fault in system_faults.faults],
        }

    gsm = gateway.gsm
    if gsm is not None:
        diagnostics["gsm"] = {
            "supply_voltage": gsm.supply_voltage,
            "firmware_version": gsm.firmware_version,
            "operator": gsm.operator,
            "signal_strength": gsm.signal_strength,
            "credit": gsm.credit,
        }

    return diagnostics


async def async_get_device_diagnostics(
        hass,
        entry: InimPrimeConfigEntry,
        device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device."""

    gateway: InimPrimeGateway = entry.runtime_data.gateway
    data = get_entry_data(entry)
    panel_log_events_coordinator = entry.runtime_data.coordinators.panel_log_events

    device_info: dict[str, Any] = {}
    for domain, dev_id in device.identifiers:
        if domain != DOMAIN:
            continue

        if "_zone_" in dev_id:
            zone_id = int(dev_id.split("_zone_")[1])
            zone = gateway.get_zone(zone_id)
            if zone:
                device_info = {"device_type": "zone", **_zone_diagnostics(zone)}

        elif "_partition_" in dev_id:
            partition_id = int(dev_id.split("_partition_")[1])
            partition = gateway.get_partition(partition_id)
            if partition:
                device_info = {"device_type": "partition", **_partition_diagnostics(partition)}

        elif dev_id.endswith("_arming_scenarios"):
            arming_scenarios = gateway.arming_scenarios
            if arming_scenarios is not None:
                device_info = {
                    "device_type": "arming_scenarios",
                    "count_active": gateway.count_active_arming_scenarios,
                    "arming_scenarios": {
                        arming_scenario_id: _arming_scenario_diagnostics(gateway, arming_scenario)
                        for arming_scenario_id, arming_scenario in arming_scenarios.items()
                    },
                }
            else:
                device_info = {"device_type": "arming_scenarios", "error": "Native not configured"}

        elif "_gsm" in dev_id:
            gsm = gateway.gsm
            if gsm is not None:
                device_info = {
                    "device_type": "gsm",
                    "supply_voltage": gsm.supply_voltage,
                    "firmware_version": gsm.firmware_version,
                    "operator": gsm.operator,
                    "signal_strength": gsm.signal_strength,
                    "credit": gsm.credit,
                }
            else:
                device_info = {"device_type": "gsm", "error": "PrimeLAN not configured"}

        else:
            device_info = {
                "device_type": "panel",
                "serial_number": data["serial_number"],
                "backends_active": gateway.backends_active,
            }
            system_faults = gateway.system_faults
            if system_faults is not None:
                device_info["supply_voltage"] = system_faults.supply_voltage
                device_info["active_faults"] = [
                    fault.name for fault in system_faults.faults
                ]
            arming_scenarios = gateway.arming_scenarios
            if arming_scenarios is not None:
                device_info["count_active_arming_scenarios"] = gateway.count_active_arming_scenarios
            if panel_log_events_coordinator is not None:
                device_info["log_events"] = panel_log_events_coordinator.last_panel_log_events

    return device_info